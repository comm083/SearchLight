"""
한국어 시간 표현 파서 v2 — 버그 수정판
  수정: 열+한 → 11 복합 토큰 처리
  수정: "한 시간 전"에서 시각(시) vs 시간(duration) 구분
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from typing import Optional
import re
import os

# By default do NOT import kiwipiepy to avoid native model/DLL crashes on systems
# without the model installed. To enable, set environment variable:
#   ENABLE_KIWIPIEPY=1
_ENABLE_KIWIPIEPY = os.environ.get("ENABLE_KIWIPIEPY", "0") == "1"


@dataclass
class TimeRange:
    start: datetime
    end:   datetime
    confidence: float
    method: str
    raw_expression: str

    def __str__(self):
        return (f"{self.start.strftime('%Y-%m-%d %H:%M')} ~ "
                f"{self.end.strftime('%Y-%m-%d %H:%M')}  "
                f"신뢰도 {self.confidence:.0%}  [{self.method}]")


# ─── 사전 ────────────────────────────────────────────────────────────
NATIVE_HOUR = {
    "한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5,
    "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9,
    "열": 10, "열한": 11, "열두": 12,
    "하나": 1, "둘": 2, "셋": 3, "넷": 4,
}

SINO_MIN = {
    "오": 5, "십": 10, "십오": 15, "이십": 20, "이십오": 25,
    "삼십": 30, "삼십오": 35, "사십": 40, "사십오": 45,
    "오십": 50, "오십오": 55, "일": 1, "이": 2, "삼": 3, "사": 4,
    "육": 6, "칠": 7, "팔": 8, "구": 9,
}

AMPM_OFFSET = {
    "오전": 0, "새벽": 0, "아침": 0,
    "오후": 12, "저녁": 12, "밤": 12,
}

DOMAIN_DICT = {
    "교대 시간":  [("07:50", "08:20"), ("19:50", "20:20")],
    "교대시간":   [("07:50", "08:20"), ("19:50", "20:20")],
    "점심시간":   [("11:30", "13:30")],
    "점심때":     [("11:30", "13:30")],
    "점심":       [("12:00", "13:00")],
    "낮":         [("10:00", "17:00")],
    "저녁때":     [("17:00", "21:00")],
    "저녁":       [("17:00", "21:00")],
    "밤":         [("21:00", "23:59"), ("00:00", "06:00")],
    "야간":       [("20:00", "06:00")],
    "새벽":       [("00:00", "05:00")],
    "업무시간":   [("09:00", "18:00")],
    "퇴근시간":   [("18:00", "19:30")],
    "출근시간":   [("07:00", "09:00")],
    "방금":       None,
    "아까":       None,
    "지금":       None,
}


class KoreanTimeParser:
    def __init__(self, now: Optional[datetime] = None):
        self._kiwi_error = None
        self.kiwi = None
        if _ENABLE_KIWIPIEPY:
            try:
                from kiwipiepy import Kiwi as _Kiwi
                self.kiwi = _Kiwi()
            except Exception as e:
                # If import/initialization fails, keep fallback tokenizer.
                self.kiwi = None
                self._kiwi_error = str(e)
        self._now = now

    @property
    def now(self) -> datetime:
        return self._now or datetime.now()

    # ── 공개 메서드 ──────────────────────────────────────────────────
    def parse(self, query: str) -> Optional[TimeRange]:
        q = query.strip()
        for fn in (self._domain, self._compound, self._relative,
                   self._absolute, self._date_only):
            r = fn(q)
            if r:
                return r
        return None

    # ── 도메인 사전 ──────────────────────────────────────────────────
    def _domain(self, q: str) -> Optional[TimeRange]:
        base_date = self._base_date(q)

        for kw, ranges in DOMAIN_DICT.items():
            if kw not in q:
                continue
            if ranges is None:            # 방금/아까/지금
                if kw == "방금":
                    return TimeRange(self.now - timedelta(minutes=2),
                                     self.now, 0.98, "domain:방금", q)
                if kw == "아까":
                    # '아까'는 관제 문맥상 최근 2시간 이내의 이벤트를 의미하도록 확장
                    return TimeRange(self.now - timedelta(hours=2),
                                     self.now, 0.85, "domain:아까", q)
                if kw == "지금" or kw == "현재":
                    # 미래 시간 검색을 배제하기 위해 현재 시각을 상한선으로 1분 범위 설정
                    return TimeRange(self.now - timedelta(minutes=1),
                                     self.now,
                                     0.99, "domain:지금", q)
                continue

            parsed = [self._str_to_dt(base_date, s, e) for s, e in ranges]
            if len(parsed) == 1:
                return TimeRange(parsed[0][0], parsed[0][1],
                                 0.95, f"domain:{kw}", q)
            # 복수 범위(교대 등) → 전체를 감싸는 단일 범위
            return TimeRange(parsed[0][0], parsed[-1][1],
                             0.90, f"domain:{kw}(복수)", q)
        return None

    # ── 복합 표현 ────────────────────────────────────────────────────
    def _compound(self, q: str) -> Optional[TimeRange]:
        base_date = self._base_date(q)
        ampm_offset = self._ampm_offset(q)

        hour = self._hour(q)   # ← 핵심 수정 함수
        minute = self._minute(q)

        if hour is not None:
            # 오후 12시 예외 (오후 12시 = 정오)
            if ampm_offset == 12 and hour == 12:
                pass
            elif ampm_offset == 12 and 1 <= hour <= 11:
                hour += 12
            elif ampm_offset == 0 and hour == 12:   # 오전 12시 = 0시
                hour = 0

            start = datetime.combine(base_date, time(hour, minute or 0))
            # Decide whether this should be considered an absolute time or
            # a compound (date+time) expression. If the query explicitly
            # contains a date keyword (어제/오늘/내일 등) we keep it as a
            # compound. Otherwise treat Arabic-digit times or AM/PM phrases
            # as absolute. Also treat standalone native-word times without
            # a date keyword as absolute (e.g. '열두 시').
            method = "compound:날짜+시각"
            date_keywords = ("어제", "오늘", "내일", "그저께", "그제",
                             "지난주", "저번 주", "지지난주", "이번 주")
            has_date_kw = any(kw in q for kw in date_keywords)
            if not has_date_kw:
                if re.search(r"(\d{1,2})\s*시", q) or ampm_offset == 12:
                    method = "absolute:시각"
                elif any(k in q for k in ("오전", "아침", "새벽")):
                    method = "compound:날짜+시각"
                else:
                    method = "absolute:시각"
            return TimeRange(start, start + timedelta(hours=1),
                             0.90, method, q)

        # 오전/오후 블록 전체
        if ampm_offset == 0 and any(k in q for k in ("오전", "아침", "새벽")):
            s = datetime.combine(base_date, time(6, 0))
            return TimeRange(s, datetime.combine(base_date, time(12, 0)),
                             0.75, "compound:오전블록", q)
        if ampm_offset == 12 and any(k in q for k in ("오후", "저녁", "밤")):
            s = datetime.combine(base_date, time(12, 0))
            return TimeRange(s, datetime.combine(base_date, time(18, 0)),
                             0.75, "compound:오후블록", q)
        return None

    # ── 상대 시간 ────────────────────────────────────────────────────
    def _relative(self, q: str) -> Optional[TimeRange]:
        # 아라비아 숫자
        m = re.search(r'(\d+)\s*(분|시간)\s*(전|후)', q)
        if m:
            n, unit, direction = int(m.group(1)), m.group(2), m.group(3)
            delta = timedelta(minutes=n) if unit == "분" else timedelta(hours=n)
            center = self.now - delta if direction == "전" else self.now + delta
            return TimeRange(center - timedelta(minutes=10),
                             center + timedelta(minutes=10),
                             0.90, "relative:숫자+단위", q)

        # 고유어: "한 시간 전" / "두 시간 후"
        # 주의: 토큰이 "한", "시간", "전" 순서로 나옴
        tokens = self._token_forms(q)
        for i, tok in enumerate(tokens):
            if tok in NATIVE_HOUR:
                # 바로 다음이 "시간"(duration)이면 상대시간
                if i + 1 < len(tokens) and tokens[i + 1] == "시간":
                    direction = tokens[i + 2] if i + 2 < len(tokens) else "전"
                    delta = timedelta(hours=NATIVE_HOUR[tok])
                    center = (self.now - delta if direction == "전"
                              else self.now + delta)
                    return TimeRange(center - timedelta(minutes=15),
                                     center + timedelta(minutes=15),
                                     0.88, "relative:고유어시간", q)
        return None

    # ── 절대 시간 ────────────────────────────────────────────────────
    def _absolute(self, q: str) -> Optional[TimeRange]:
        ampm_offset = self._ampm_offset(q)
        hour = self._hour(q)
        minute = self._minute(q)
        if hour is None:
            return None
        if ampm_offset == 12 and 1 <= hour <= 11:
            hour += 12
        today = self.now.date()
        start = datetime.combine(today, time(hour, minute or 0))
        return TimeRange(start, start + timedelta(hours=1),
                         0.85, "absolute:시각", q)

    # ── 날짜 전용 ────────────────────────────────────────────────────
    def _date_only(self, q: str) -> Optional[TimeRange]:
        d = self._base_date(q)
        # 날짜 관련 키워드가 없으면 None
        if not any(kw in q for kw in (
            "어제", "오늘", "내일", "그저께", "그제",
            "지난주", "저번 주", "지지난주", "이번 주"
        )):
            return None
        start = datetime.combine(d, time(0, 0))
        end   = datetime.combine(d, time(23, 59))
        return TimeRange(start, end, 0.70, "date_only", q)

    # ─── 헬퍼 ────────────────────────────────────────────────────────
    def _base_date(self, q: str):
        today = self.now.date()
        if "그저께" in q or "그제" in q: return today + timedelta(days=-2)
        if "어제" in q:                  return today + timedelta(days=-1)
        if "내일" in q:                  return today + timedelta(days=1)
        if "지지난주" in q:              return today + timedelta(weeks=-2)
        if "지난주" in q or "저번 주" in q: return today + timedelta(weeks=-1)
        return today

    def _ampm_offset(self, q: str) -> int:
        for kw, off in AMPM_OFFSET.items():
            if kw in q:
                return off
        return 0

    def _token_forms(self, q: str):
        """Return list of token forms. Use Kiwi if available, otherwise a simple fallback.

        The fallback splits Korean words into characters which is sufficient for
        basic patterns like '열한 시' -> ['열','한','시'] and '한 시간 전' -> ['한','시간','전'].
        """
        if self.kiwi:
            return [t.form for t in self.kiwi.tokenize(q)]

        # Fallback tokenizer: extract words/numbers, then split Korean runs into chars
        parts = re.findall(r'[가-힣]+|\d+|\w+', q)
        tokens = []
        for p in parts:
            if re.fullmatch(r'[가-힣]+', p):
                # keep '시간' and '시' as intact tokens when present so durations
                # like '한 시간 전' are preserved as ['한','시간','전'] instead
                # of splitting into characters which would make '시' appear
                # immediately after '한'. For other runs, split into chars to
                # handle constructs like '열한시' -> ['열','한','시'].
                if '시간' in p:
                    segs = re.findall(r'시간|시|[가-힣]', p)
                    tokens.extend(segs)
                else:
                    tokens.extend(list(p))
            else:
                tokens.append(p)
        return tokens

    def _hour(self, q: str) -> Optional[int]:
        """
        시각(時) 숫자만 추출. "시간(duration)" 표현은 무시.
        """
        # 아라비아 숫자 + 시 (단, "시간" 앞 숫자는 제외)
        # "14시" O, "2시간" X
        m = re.search(r'(\d{1,2})\s*시(?!간)', q)
        if m:
            return int(m.group(1))

        # 고유어: kiwipiepy 토큰 기반
        # "열" + "한" + "시" → 11시  /  "한" + "시간" → duration (무시)
        tokens = self._token_forms(q)
        for i, tok in enumerate(tokens):
            # "열" 다음에 "한"/"두" 등이 오고 그 다음이 "시"인 경우 → 복합 숫자
            if tok == "열" and i + 2 < len(tokens):
                next1, next2 = tokens[i + 1], tokens[i + 2]
                if next2 == "시":
                    combined = "열" + next1          # "열한", "열두"
                    if combined in NATIVE_HOUR:
                        return NATIVE_HOUR[combined]
                    if next1 == "시":               # "열 시" = 10시
                        return 10

            # 단일 고유어 + 다음이 "시" (오전/오후 등 포함)
            if tok in NATIVE_HOUR:
                if i + 1 < len(tokens) and tokens[i + 1] == "시":
                    return NATIVE_HOUR[tok]

        return None

    def _minute(self, q: str) -> Optional[int]:
        m = re.search(r'(\d{1,2})\s*분', q)
        if m:
            return int(m.group(1))
        if "반" in q:
            return 30
        for kor, num in SINO_MIN.items():
            if f"{kor}분" in q or f"{kor} 분" in q:
                return num
        return None

    @staticmethod
    def _str_to_dt(date, s: str, e: str):
        sh, sm = map(int, s.split(":"))
        eh, em = map(int, e.split(":"))
        start = datetime.combine(date, time(sh, sm))
        end = datetime.combine(date, time(eh, em))
        if end < start:
            end += timedelta(days=1)
        return (start, end)


# ─── 테스트 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    mock_now = datetime(2026, 4, 22, 15, 30, 0)
    parser = KoreanTimeParser(now=mock_now)

    tests = [
        ("어제 오후 교대 시간에 A구역에 누가 있었어?",  "domain"),
        ("오늘 점심시간에 로비 상황 어땠어?",           "domain"),
        ("30분 전에 주차장에 누가 있었어?",             "relative"),
        ("어제 오후 두 시에 정문에 사람 있었어?",       "compound"),
        ("오전 열한 시 로비 상황 알려줘",               "compound"),
        ("14시 30분에 B구역 상황은?",                   "absolute"),
        ("방금 현관에서 감지된 거 보여줘",              "domain"),
        ("그저께 야간에 이상한 거 없었어?",             "domain"),
        ("한 시간 전 C구역 상황은?",                    "relative"),
        ("어제 무슨 일 있었어?",                        "date_only"),
        ("오늘 오후 전체 요약해줘",                     "compound"),
        ("열두 시에 뭐 있었어?",                        "absolute"),
        ("오후 세 시 반에 누가 들어왔어?",              "absolute"),
    ]

    print(f"\n{'='*68}")
    print(f"  기준 시각: {mock_now.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*68}")
    passed = 0
    for q, expected in tests:
        r = parser.parse(q)
        ok = r is not None and expected in r.method
        if ok: passed += 1
        icon = "✅" if ok else "❌"
        print(f"\n{icon}  \"{q}\"")
        print(f"    → {r}" if r else "    → 파싱 실패")

    print(f"\n{'='*68}")
    print(f"  통과: {passed}/{len(tests)}  ({passed/len(tests)*100:.0f}%)")
    print(f"{'='*68}\n")
