import os
import sys
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

# 모듈 경로 추가 (필요 시)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.nlp.sentence_correction import correct_stt_text
from ai.intent_classifier.classifier import IntentClassifier

load_dotenv()


TIME_KEYWORDS = [
    "어제", "오늘", "내일", "최근", "아까", "방금", "지금", "이전", "오래된", "옛날",
    "오전", "오후", "새벽", "아침", "점심", "저녁", "밤",
    "시간", "시각", "분", "초", "언제", "몇 시", "몇시",
    "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일",
    "주말", "평일", "이번 주", "지난주", "지난 주",
]

OLDEST_KEYWORDS = ["오래된", "옛날", "예전", "처음", "가장 오래", "오래전", "이전"]
NEWEST_KEYWORDS = ["최근", "방금", "아까", "요즘", "새로운", "가장 최근", "최신"]

PERSON_KEYWORDS = [
    "사람", "남자", "여자", "남성", "여성", "아이", "어린이", "청소년", "노인", "어르신",
    "손님", "고객", "직원", "점원", "알바", "용의자", "도둑", "범인", "침입자",
    "누군가", "누구", "인물", "행인", "보행자",
    "들어", "나가", "뛰", "걷", "서있", "앉", "쓰러", "싸우", "훔치", "때리",
    "입고", "들고", "메고", "옷", "가방", "모자",
]

def has_time_keyword(text: str) -> bool:
    return any(kw in text for kw in TIME_KEYWORDS)

def has_person_keyword(text: str) -> bool:
    return any(kw in text for kw in PERSON_KEYWORDS)


def rewrite_from_perspectives(text: str, client: OpenAI) -> dict:
    """질문을 경비원/등장인물/(시간) 관점으로 재작성. 시간 키워드 없으면 시간 관점 제외."""
    include_time = has_time_keyword(text)
    include_person = has_person_keyword(text)

    num = 1
    perspective_lines = f"{num}. 경비원 관점: 이상 상황·보안 위협 중심으로 재해석"
    json_keys = ["경비원"]

    if include_person:
        num += 1
        perspective_lines += f"\n{num}. 등장인물 관점: 영상 속 인물의 행동·특징 중심으로 재해석"
        json_keys.append("등장인물")
        num += 1
        perspective_lines += f"\n{num}. 행동 관점: 인물이 취한 구체적인 행동·동작 중심으로 재해석"
        json_keys.append("행동")

    if include_time:
        num += 1
        perspective_lines += f"\n{num}. 시간 관점: 사건 발생 시각·시간대 중심으로 재해석"
        json_keys.append("시간")

    json_template = "{" + ", ".join(f'"{k}": "..."' for k in json_keys) + "}"

    prompt = f"""경비 CCTV 시스템에서 다음 질문을 관점별로 재작성하세요.
원본 질문: "{text}"

{perspective_lines}

JSON으로만 출력하세요 (설명 없이):
{json_template}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```json"):
        raw = raw[7:-3].strip()
    elif raw.startswith("```"):
        raw = raw[3:-3].strip()
    return json.loads(raw)

def main():
    # 한글 출력을 위한 인코딩 설정 (Windows 대응)
    if sys.platform == "win32":
        try:
            # sys.stdout.reconfigure는 Python 3.7+에서 지원하며 더 안전합니다.
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    print("="*60)
    print("      SearchLight AI Intelligent Chatbot System")
    print("="*60)

    # 1. 모델 로드 및 시스템 초기화
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        print("[1/4] 문장 교정 모델(KoBART) 준비 중...")
        correct_stt_text("시스템 체크")

        print("[2/4] 의도 분류 모델(KoELECTRA) 로드 중...")
        classifier = IntentClassifier()
        model_path = os.path.join("model", "koelectra_finetuned")
        if os.path.exists(model_path):
            classifier.load_model(model_path)
            print(f" -> 학습된 모델 로드 완료: {model_path}")
        else:
            print(" -> [경고] 학습된 모델을 찾을 수 없어 기본 모델을 사용합니다.")

        print("[3/4] 유사 장면 검색용 FAISS 인덱스 구축 중...")
        sbert_model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        json_path = os.path.join("ai", "data", "mp4_JsonData.json")

        with open(json_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
            # 영상의 요약(summary) 필드를 검색 대상으로 설정
            db_descriptions = [item["summary"] for item in scene_data]

        db_embeddings = sbert_model.encode(db_descriptions).astype('float32')
        faiss.normalize_L2(db_embeddings)  # 코사인 유사도를 위해 L2 정규화
        dimension = db_embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner Product = 코사인 유사도 (정규화 후)
        index.add(db_embeddings)
        print(f" -> {len(db_descriptions)}개의 영상 데이터로 인덱스 구축 완료.")
        print("[4/4] OpenAI 클라이언트 준비 완료.")

    except Exception as e:
        print(f"\n[오류] 시스템 초기화 중 문제가 발생했습니다: {e}")
        return

    print("\n[시스템 준비 완료] 대화를 시작합니다. (종료하려면 'q' 입력)")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n사용자 질문: ").strip()
        except EOFError:
            break

        if not user_input:
            continue
        if user_input.lower() == 'q':
            print("시스템을 종료합니다. 감사합니다.")
            break

        print("\n" + "." * 10 + " 분석 중 " + "." * 10)

        # Step 1: 문장 교정 (KoBART)
        corrected_text = correct_stt_text(user_input)
        print(f"[Step 1] 문장 교정 결과: {corrected_text}")

        # Step 2: 3가지 관점으로 질문 재작성 (GPT)
        try:
            perspectives = rewrite_from_perspectives(corrected_text, openai_client)
        except Exception as e:
            print(f" -> [경고] 관점 재작성 실패, 원문 사용: {e}")
            perspectives = {"경비원": corrected_text, "등장인물": corrected_text, "시간": corrected_text}

        print(f"[Step 2] 관점별 질문 재작성:")
        for label, text in perspectives.items():
            print(f"  [{label}] {text}")

        # Step 3: 각 관점별 의도 분류 → 가장 높은 신뢰도로 진행 (KoELECTRA)
        best_query = corrected_text
        best_intent = None
        best_confidence = -1
        best_perspective_label = "원문"

        for label, text in perspectives.items():
            result = classifier.predict(text)
            print(f"  [{label}] 의도: {result['intent_label']} (확률: {result['confidence']:.2f})")
            if result["confidence"] > best_confidence:
                best_confidence = result["confidence"]
                best_intent = result
                best_query = text
                best_perspective_label = label

        print(f"[Step 3] 선택된 관점: [{best_perspective_label}] - {best_intent['intent_label']} (확률: {best_confidence:.2f})")
        print(f" -> 검색 쿼리: {best_query}")

        # Step 4: 관련 장면 검색 (SBERT + FAISS, 코사인 유사도)
        # 원문(70%) + 관점 쿼리(30%) 가중 앙상블: 원문이 검색의 주축을 유지하도록 함
        query_texts = list(dict.fromkeys([corrected_text, best_query]))  # 중복 제거
        query_embeddings = sbert_model.encode(query_texts).astype('float32')
        faiss.normalize_L2(query_embeddings)
        if len(query_texts) == 1:
            ensemble_embedding = query_embeddings[0:1]
        else:
            weights = np.array([0.7, 0.3])
            ensemble_embedding = np.average(query_embeddings, axis=0, weights=weights).reshape(1, -1).astype('float32')
            faiss.normalize_L2(ensemble_embedding)

        # FAISS로 의미 유사한 상위 후보 추출
        is_oldest = any(kw in corrected_text for kw in OLDEST_KEYWORDS)
        is_newest = any(kw in corrected_text for kw in NEWEST_KEYWORDS)

        k = min(len(scene_data), 3 if (is_oldest or is_newest) else 1)
        scores, indices = index.search(ensemble_embedding, k)
        candidates = [scene_data[idx] for idx in indices[0]]

        # 날짜 키워드가 있으면 후보 내에서 날짜 기준 재정렬
        if is_oldest or is_newest:
            candidates = sorted(
                candidates,
                key=lambda x: x.get("event_date", ""),
                reverse=is_newest
            )
            direction = "가장 오래된" if is_oldest else "가장 최근"
            print(f"[Step 4] 의미 유사 후보 {k}개 중 날짜 기준 ({direction}) 선택")
        else:
            print(f"[Step 4] 가장 유사한 장면 검색 성공 (유사도 점수: {scores[0][0]:.4f})")

        best_match = candidates[0]

        # Step 5: 결과 출력
        print(f"\n[Step 5] 최종 리턴")
        print(f" ▶ 매칭 영상: {best_match.get('video_filename', 'N/A')}")
        print(f" ▶ 발생 시각: {best_match.get('event_date', 'N/A')}")
        print(f" ▶ 요약 내용: {best_match.get('summary', 'N/A')}")

        if "video_filename" in best_match:
            video_url = f"/static/mp4Data/{best_match['video_filename']}"
            print(f" ▶ 영상 경로: {video_url}")
        else:
            print(" ▶ 매칭된 영상을 찾을 수 없습니다.")

        print("-" * 60)

if __name__ == "__main__":
    main()
