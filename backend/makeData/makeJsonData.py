import base64
import json
import re
import os
import sys
import tempfile
import random
from datetime import datetime, timedelta
from openai import OpenAI
import cv2
from dotenv import load_dotenv
from supabase import create_client, Client
import easyocr

load_dotenv()

api_key        = os.getenv("OPENAI_API_KEY")
SUPABASE_URL   = os.getenv("SUPABASE_URL")
# service_role 키 우선 사용 (RLS 우회) → 없으면 anon 키로 폴백
SUPABASE_KEY   = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
STORAGE_BUCKET = "cctv-clips"

# 랜덤 타임스탬프 생성 시 날짜 중복 방지용 추적 집합
_used_random_dates: set = set()

def _generate_random_timestamp() -> str:
    """OCR 실패 시 현재 기준 1주일 이내 랜덤 타임스탬프 생성 (날짜 중복 없음)."""
    now = datetime.now()
    available = [now.date() - timedelta(days=d) for d in range(7) if (now.date() - timedelta(days=d)) not in _used_random_dates]
    if not available:
        # 7일치 모두 소진 시 중복 허용
        date = now.date() - timedelta(days=random.randint(0, 6))
    else:
        date = random.choice(available)
    _used_random_dates.add(date)
    h  = random.randint(0, 23)
    m  = random.randint(0, 59)
    s  = random.randint(0, 59)
    return f"{date} {h:02d}:{m:02d}:{s:02d}"


# ─────────────────────────────────────────────
# Supabase 클라이언트
# ─────────────────────────────────────────────
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(".env 파일에 SUPABASE_URL, SUPABASE_SERVICE_KEY(또는 SUPABASE_KEY)를 설정해주세요.")
    key_type = "service_role" if os.getenv("SUPABASE_SERVICE_KEY") else "anon"
    print(f"  [Supabase] {key_type} 키로 연결 중...")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────────
# OCR: 좌측 상단 타임스탬프 읽기
# ─────────────────────────────────────────────
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        print("  [OCR] EasyOCR 초기화 중 (첫 실행 시 모델 다운로드)...")
        # 영어 전용: 한글 오인식 방지 / verbose=False: Windows cp949 인코딩 충돌 방지
        _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _ocr_reader


def _fix_ocr_chars(text: str) -> str:
    """
    LCD 폰트 숫자를 알파벳으로 오인식하는 패턴 교정.
    실측 매핑 예: 2026-04-27 → '2IZF-[4-27' 또는 '2ZE-[-건7'
      0 → I, [, ]
      2 → Z
      6 → F, E (LCD 6의 획이 F 또는 E로 보임)
      8 → B
    """
    table = str.maketrans({
        'I': '0',   # 0 → I
        '[': '0',   # 0 → [
        ']': '0',
        'Z': '2',   # 2 → Z
        'z': '2',
        'F': '6',   # 6 → F
        'E': '6',   # 6 → E (새로 추가)
        'G': '6',
        'O': '0', 'Q': '0', 'U': '0', 'u': '0',  # U/u → 0
        'l': '1', '|': '1',
        'B': '8',
        'S': '5',
    })
    # 알파벳 교정 (한글은 제외 — 이후 _strip_non_ts로 제거)
    return ''.join(
        ch.translate(table) if ch.isalpha() and not ('가' <= ch <= '힣') else ch
        for ch in text
    )


def _strip_non_ts(text: str) -> str:
    """타임스탬프 구성 문자(숫자·'-'·':'·공백)만 남기고 나머지 제거.
    OCR에서 ':'를 '.'로 오인식하는 경우도 ':'로 정규화."""
    text = text.replace('.', ':')   # 08.26 → 08:26
    return re.sub(r'[^\d\-: ]', '', text)


def _try_tesseract(img_gray) -> str:
    """Tesseract가 설치된 경우 사용. 없으면 빈 문자열 반환."""
    try:
        import pytesseract
        # LCD/디지털 폰트에 최적화된 설정
        cfg = '--psm 7 --oem 0 -c tessedit_char_whitelist=0123456789-: '
        return pytesseract.image_to_string(img_gray, config=cfg).strip()
    except Exception:
        return ""


def read_timestamp_from_frame(frame) -> str | None:
    """
    프레임 좌측 상단 흰색 LCD 타임스탬프를 OCR로 읽어
    'YYYY-MM-DD HH:MM:SS' 형식으로 반환. 실패 시 None.
    """
    h, w = frame.shape[:2]
    roi = frame[0:max(1, int(h * 0.15)), 0:max(1, int(w * 0.7))]

    # 흰 픽셀(>200)만 추출 → 반전 없이 흰 글씨 on 검정 배경 유지
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # 3배 확대 (nearest: 픽셀 경계 보존)
    roi_3x     = cv2.resize(roi,          None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
    thresh_3x  = cv2.resize(thresh_white, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)

    reader = get_ocr_reader()
    candidates = []

    for img in [roi_3x, cv2.cvtColor(thresh_3x, cv2.COLOR_GRAY2BGR)]:
        # allowlist로 숫자+자주 혼동되는 알파벳만 허용 → 5/6 등 구분 정확도 향상
        results = reader.readtext(
            img, detail=0, paragraph=False,
            allowlist='0123456789IZFEGOQlBSUu-:. []'
        )
        text = " ".join(results).strip()
        if text:
            candidates.append(text)

    # Tesseract (설치된 경우)
    tess = _try_tesseract(thresh_3x)
    if tess:
        candidates.append(tess)

    def _parse(text):
        corrected = _strip_non_ts(_fix_ocr_chars(text))
        print(f"  [OCR]  정제 후: '{corrected}'")
        # 패턴 1: YYYY-MM-DD HH:MM:SS (엄격)
        m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', corrected)
        if m:
            return f"{m.group(1)} {m.group(2)}"
        # 패턴 2: 초 없는 경우 YYYY-MM-DD HH:MM → HH:MM:00 (패턴3보다 먼저 체크)
        m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}[:.]\d{2})(?!\d)', corrected)
        if m:
            time_str = m.group(2).replace('.', ':')
            return f"{m.group(1)} {time_str}:00"
        # 패턴 3: 구분자 유연 (연도 3자리 등 비정상 OCR 대응)
        m = re.search(r'(\d{3,4})\D{0,2}(\d{1,2})\D{0,2}(\d{1,2})\D+(\d{2})[^\d](\d{2})[^\d](\d{2})', corrected)
        if m:
            y, mo, d, hh, mi, ss = m.groups()
            if len(y) == 3:
                y = y[0] + '0' + y[1:]   # '226' → '2026'
            return f"{y}-{mo.zfill(2)}-{d.zfill(2)} {hh.zfill(2)}:{mi.zfill(2)}:{ss.zfill(2)}"
        return None

    for raw in candidates:
        print(f"  [OCR] 원본: '{raw}' → 교정: '{_fix_ocr_chars(raw)}'")
        result = _parse(raw)
        if result:
            return result

    print("  [OCR 경고] 타임스탬프를 인식하지 못했습니다 → event_date = NULL")
    return None


# ─────────────────────────────────────────────
# 영상 처리: 분석 프레임 + 사람 감지 클립 추출
# ─────────────────────────────────────────────
MIN_FRAMES   = 5    # GPT에 전달할 최소 프레임 수
MAX_FRAMES   = 20   # GPT에 전달할 최대 프레임 수 (페이로드 초과 방지)
MOTION_AREA  = 800  # 모션 감지 최소 면적 (픽셀²)


def _detect_motion(prev_gray, curr_gray) -> bool:
    """프레임 간 차분으로 움직임(사람 포함)을 감지합니다."""
    diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return any(cv2.contourArea(c) > MOTION_AREA for c in contours)


def encode_video_and_extract_clips(video_path: str):
    """
    Returns:
        base64frames (list[str])  : GPT 분석용 base64 프레임
        person_clips (list[tuple]): [(start_sec, end_sec, tmp_path), ...]
        start_timestamp (str|None): OCR로 읽은 영상 시작 시각
    """
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 3.0
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    interval_normal = max(1, int(fps * 10))  # 기본: 10초마다
    interval_motion = max(1, int(fps * 5))   # 모션 감지 시: 5초마다

    # 첫 프레임에서 타임스탬프 OCR
    start_timestamp = None
    ret, first_frame = video.read()
    if ret:
        start_timestamp = read_timestamp_from_frame(first_frame)
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    candidates = []            # (frame_idx, buffer, has_motion)
    motion_frame_indices = []
    prev_motion_gray = None   # 5초 간격 체크용 (직전 체크포인트 프레임)
    cur = 0

    while video.isOpened():
        success, frame = video.read()
        if not success:
            break

        if cur % interval_motion == 0:
            curr_gray = cv2.cvtColor(cv2.resize(frame, (320, 240)), cv2.COLOR_BGR2GRAY)
            # prev_motion_gray: 5초 전 체크포인트 프레임과 비교 (직전 프레임과 비교 시 모션 미감지 버그 수정)
            has_motion = _detect_motion(prev_motion_gray, curr_gray) if prev_motion_gray is not None else False
            _, buffer = cv2.imencode(".jpg", frame)
            candidates.append((cur, buffer, has_motion))
            if has_motion:
                motion_frame_indices.append(cur)
            prev_motion_gray = curr_gray

        cur += 1

    video.release()
    total_frames = cur or total_frames

    # 분석용 base64 프레임 (모션 구간은 5초, 그 외 10초)
    base64frames = [
        base64.b64encode(buf).decode("utf-8")
        for idx, buf, has_motion in candidates
        if has_motion or idx % interval_normal == 0
    ]

    # 프레임이 MIN_FRAMES보다 적으면 후보 전체에서 균등하게 보충
    if len(base64frames) < MIN_FRAMES and candidates:
        step = max(1, len(candidates) // MIN_FRAMES)
        extra = [
            base64.b64encode(buf).decode("utf-8")
            for i, (_, buf, _) in enumerate(candidates)
            if i % step == 0
        ]
        # 중복 제거 후 병합
        seen = set(base64frames)
        for f in extra:
            if f not in seen:
                base64frames.append(f)
                seen.add(f)
        base64frames = base64frames[:max(MIN_FRAMES, len(base64frames))]

    # 프레임 수 상한 적용 (균등 샘플링)
    if len(base64frames) > MAX_FRAMES:
        step = len(base64frames) / MAX_FRAMES
        base64frames = [base64frames[int(i * step)] for i in range(MAX_FRAMES)]

    print(f"  [프레임] 총 {cur}프레임 / 분석용 {len(base64frames)}장 / 모션 감지 {len(motion_frame_indices)}회")

    # 모션 감지 구간 → 클립 추출
    person_clips = []
    if motion_frame_indices:
        gap_threshold = int(fps * 15)  # 15초 이내면 같은 구간으로 묶음
        groups = []
        gs, ge = motion_frame_indices[0], motion_frame_indices[0]
        for idx in motion_frame_indices[1:]:
            if idx - ge <= gap_threshold:
                ge = idx
            else:
                groups.append((gs, ge))
                gs, ge = idx, idx
        groups.append((gs, ge))

        video2 = cv2.VideoCapture(video_path)
        width  = int(video2.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video2.get(cv2.CAP_PROP_FRAME_HEIGHT))

        for i, (s_frame, e_frame) in enumerate(groups):
            s_frame = max(0, s_frame - int(fps * 2))          # 앞 2초 여유
            e_frame = min(total_frames - 1, e_frame + int(fps * 2))  # 뒤 2초 여유
            s_sec   = round(s_frame / fps, 2)
            e_sec   = round(e_frame / fps, 2)

            tmp_path = os.path.join(
                tempfile.gettempdir(),
                f"clip_{i+1}_{os.path.basename(video_path)}"
            )
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

            video2.set(cv2.CAP_PROP_POS_FRAMES, s_frame)
            for _ in range(e_frame - s_frame + 1):
                ok, frm = video2.read()
                if not ok:
                    break
                writer.write(frm)
            writer.release()
            person_clips.append((s_sec, e_sec, tmp_path))

        video2.release()

    return base64frames, person_clips, start_timestamp


# ─────────────────────────────────────────────
# GPT 영상 분석
# ─────────────────────────────────────────────
ANALYSIS_PROMPT = """
당신은 프로 경비원입니다. 동영상의 프레임이 순서대로 주어집니다. 각 프레임 간의 차이점을 알려주고, 문제가 발생하는지 분석해야합니다.
경비원의 입장에서 상황을 설명하고, 등장 인물 수·복장·행동, 발생 시각, 이상 상황 등을 포함하여 한국어로 상세한 요약을 작성하세요.
출력 예:
{
  "summary": "..."
}
"""

def generate_intent_sentences(client: OpenAI, summary: str) -> dict:
    """GPT로 요약을 5가지 의도별 설명 문장으로 분리 생성합니다."""
    prompt = f"""다음은 CCTV 영상 분석 요약입니다:

[요약]: {summary}

위 내용을 바탕으로 아래 5가지 의도 유형별 설명 문장을 각각 한 문장씩 한국어로 작성해주세요.
- time_sent: 이 영상에서 사건이 발생한 시간/시각 중심 설명
- count_sent: 이 영상에 등장한 인원 수나 사물 개수 중심 설명
- action_sent: 이 영상에서 감지된 주요 행동/동작 중심 설명
- info_sent: 이 영상의 전체 상황을 간략하게 요약한 설명
- error_sent: 이 영상에서 카메라나 시스템 이상 여부 설명

JSON으로만 출력하세요 (설명 없이):
{{"time_sent": "...", "count_sent": "...", "action_sent": "...", "info_sent": "...", "error_sent": "..."}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```json"):
            raw = raw[7:].rsplit("```", 1)[0].strip()
        elif raw.startswith("```"):
            raw = raw[3:].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  [의도 문장 생성 실패] {e}")
        return {
            "time_sent": "", "count_sent": "", "action_sent": "",
            "info_sent": summary[:200], "error_sent": ""
        }


def analyze_frames(image_list: list) -> dict:
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
    client = OpenAI(api_key=api_key)
    contents = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
        for img in image_list
    ]
    contents.append({"type": "text", "text": ANALYSIS_PROMPT})
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role": "user", "content": contents}],
        timeout=120,
    )
    raw = response.choices[0].message.content.strip()
    if not raw:
        print("  [GPT 경고] 빈 응답 수신. 기본값으로 대체합니다.")
        return {"summary": "GPT 분석 결과 없음", "frames": []}

    if raw.startswith("```json"):
        raw = raw[7:].rsplit("```", 1)[0].strip()
    elif raw.startswith("```"):
        raw = raw[3:].rsplit("```", 1)[0].strip()

    # JSON 블록만 추출 (앞뒤 설명 텍스트 제거)
    json_start = raw.find('{')
    json_end   = raw.rfind('}')
    if json_start != -1 and json_end != -1:
        raw = raw[json_start:json_end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [GPT 경고] JSON 파싱 실패: {e}\n  원본 응답: {raw[:200]}")
        return {"summary": raw[:500], "frames": []}


# ─────────────────────────────────────────────
# Supabase Storage 클립 업로드
# ─────────────────────────────────────────────
def upload_clip(supabase: Client, clip_path: str, storage_name: str) -> str:
    """클립을 Supabase Storage에 업로드하고 공개 URL을 반환합니다."""
    with open(clip_path, 'rb') as f:
        data = f.read()
    supabase.storage.from_(STORAGE_BUCKET).upload(
        path=storage_name,
        file=data,
        file_options={"content-type": "video/mp4", "upsert": "true"}
    )
    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_name)


# ─────────────────────────────────────────────
# Supabase 테이블/버킷 생성 SQL 출력
# ─────────────────────────────────────────────
def print_schema_sql():
    print("""
-- ================================================================
-- SearchLight CCTV 스키마
-- Supabase 대시보드 > SQL Editor 에서 아래 SQL을 실행하세요.
-- ================================================================

-- 1. CCTV 영상 분석 결과 테이블
CREATE TABLE IF NOT EXISTS cctv_videos (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    video_filename  TEXT        NOT NULL UNIQUE,
    event_date      TIMESTAMPTZ,                      -- OCR로 읽은 영상 시작 시각
    summary         TEXT,                             -- GPT 생성 요약
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 의도별 설명 문장 테이블 (같은 video_id로 연결)
CREATE TABLE IF NOT EXISTS cctv_intents (
    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id    UUID    REFERENCES cctv_videos(id) ON DELETE CASCADE,
    time_sent   TEXT,   -- 시간 관련 설명 문장
    count_sent  TEXT,   -- 사람 수 관련 설명 문장
    action_sent TEXT,   -- 행동 관련 설명 문장
    info_sent   TEXT,   -- 정보 요약 문장
    error_sent  TEXT,   -- 오류 감지 문장
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 사람 감지 클립 테이블
CREATE TABLE IF NOT EXISTS person_clips (
    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id    UUID    REFERENCES cctv_videos(id) ON DELETE CASCADE,
    clip_url    TEXT    NOT NULL,        -- Supabase Storage 공개 URL
    start_sec   FLOAT,                  -- 클립 시작 (초)
    end_sec     FLOAT,                  -- 클립 종료 (초)
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 인덱스
CREATE INDEX IF NOT EXISTS idx_cctv_videos_event_date ON cctv_videos(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_cctv_intents_video_id  ON cctv_intents(video_id);
CREATE INDEX IF NOT EXISTS idx_person_clips_video_id  ON person_clips(video_id);

-- 4. Storage 버킷 생성 (이미 있으면 건너뜀)
INSERT INTO storage.buckets (id, name, public)
VALUES ('cctv-clips', 'cctv-clips', true)
ON CONFLICT (id) DO NOTHING;
-- ================================================================
""")


# ─────────────────────────────────────────────
# 단일 영상 처리
# ─────────────────────────────────────────────
def process_video(video_path: str):
    supabase = get_supabase_client()
    video_file = os.path.basename(video_path)
    print(f"\n[처리] {video_file}")

    # 중복 처리 방지
    existing = supabase.table('cctv_videos').select('id').eq('video_filename', video_file).execute()
    if existing.data:
        print("  -> 이미 처리된 영상입니다. 건너뜁니다.")
        return

    # 프레임 추출 + 클립 추출 + 타임스탬프 OCR
    frames, person_clips, start_timestamp = encode_video_and_extract_clips(video_path)
    if not frames:
        print("  -> 프레임을 추출할 수 없습니다.")
        return

    if start_timestamp is None:
        start_timestamp = _generate_random_timestamp()
        print(f"  [OCR 실패] 랜덤 타임스탬프 할당: {start_timestamp}")

    print(f"  분석 프레임: {len(frames)}장 | 사람 감지 클립: {len(person_clips)}개 | 시작 시각: {start_timestamp}")

    # GPT 분석
    print(f"  GPT 분석 중... ({len(frames)}프레임 전송)")
    try:
        video_info = analyze_frames(frames)
    except Exception as e:
        print(f"  -> [GPT 실패] {type(e).__name__}: {e}")
        video_info = {"summary": f"GPT 분석 실패: {e}", "frames": []}

    # cctv_videos 저장 (frames 컬럼 제거)
    result = supabase.table('cctv_videos').insert({
        "video_filename": video_file,
        "event_date":     start_timestamp,
        "summary":        video_info.get("summary", ""),
    }).execute()
    video_id = result.data[0]['id']
    print(f"  -> cctv_videos 저장 완료 (id: {video_id})")

    # 의도별 문장 생성 및 cctv_intents 저장
    print("  의도별 문장 생성 중 (GPT)...")
    client_obj = OpenAI(api_key=api_key)
    intent_sentences = generate_intent_sentences(client_obj, video_info.get("summary", ""))
    try:
        supabase.table('cctv_intents').insert({
            "video_id":    video_id,
            "time_sent":   intent_sentences.get("time_sent", ""),
            "count_sent":  intent_sentences.get("count_sent", ""),
            "action_sent": intent_sentences.get("action_sent", ""),
            "info_sent":   intent_sentences.get("info_sent", ""),
            "error_sent":  intent_sentences.get("error_sent", ""),
        }).execute()
        print(f"  -> cctv_intents 저장 완료")
    except Exception as e:
        print(f"  -> [cctv_intents 저장 실패] {e}")

    # 사람 감지 클립 → Storage 업로드 → person_clips 저장
    for i, (s_sec, e_sec, clip_path) in enumerate(person_clips):
        storage_name = f"{os.path.splitext(video_file)[0]}_clip{i+1}_{int(s_sec)}s-{int(e_sec)}s.mp4"
        try:
            clip_url = upload_clip(supabase, clip_path, storage_name)
            supabase.table('person_clips').insert({
                "video_id":  video_id,
                "clip_url":  clip_url,
                "start_sec": s_sec,
                "end_sec":   e_sec,
            }).execute()
            print(f"  -> 클립 업로드: {storage_name} ({s_sec}s ~ {e_sec}s)")
        except Exception as e:
            print(f"  -> 클립 업로드 실패: {e}")
        finally:
            if os.path.exists(clip_path):
                os.remove(clip_path)


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description='CCTV 영상을 분석하여 Supabase에 저장합니다.')
    parser.add_argument('--schema', action='store_true', help='테이블 생성 SQL 출력 후 종료')
    parser.add_argument('--video',  type=str, help='처리할 단일 영상 파일 경로')
    parser.add_argument('--dir',    type=str, help='처리할 영상 디렉토리 경로')
    args = parser.parse_args()

    if args.schema:
        print_schema_sql()
        return

    if args.video:
        if not os.path.exists(args.video):
            print(f"오류: 파일을 찾을 수 없습니다: {args.video}")
            return
        process_video(args.video)
        return

    # 기본 경로: backend/static/mp4Data
    video_dir = args.dir or os.path.join(os.path.dirname(__file__), "..", "static", "mp4Data")
    if not os.path.exists(video_dir):
        print(f"오류: 디렉토리를 찾을 수 없습니다: {video_dir}")
        return

    video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    print(f"총 {len(video_files)}개 영상 처리 시작...")
    for vf in video_files:
        try:
            process_video(os.path.join(video_dir, vf))
        except Exception as e:
            print(f"  -> 실패: {vf} ({e})")
    print("\n모든 작업 완료!")


if __name__ == "__main__":
    main()
