import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트를 경로에 추가 (ai 모듈 접근용)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# KoBART 문장 교정 (선택적 로드)
try:
    from ai.nlp.sentence_correction import correct_stt_text as _correct_stt_text
    _HAS_KOBART = True
except Exception:
    _HAS_KOBART = False

# KoELECTRA 의도 분류 (선택적 로드)
try:
    from ai.intent_classifier.classifier import IntentClassifier as _IntentClassifier
    _HAS_KOELECTRA = True
except Exception:
    _HAS_KOELECTRA = False


# ── 키워드 상수 ──────────────────────────────────────────────────────
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

COUNT_KEYWORDS = [
    "몇 명", "몇명", "몇 대", "몇대", "몇 번", "몇번", "몇 회", "몇회",
    "총", "집계", "통계", "인원", "명수", "대수",
]

ACTION_KEYWORDS = [
    "폭행", "절도", "훔치", "도둑", "침입", "담 넘", "싸움", "싸우", "때리",
    "쓰러", "뛰어", "도망", "낙서", "파손", "난동", "흉기", "강도", "강제",
]

SUMMARY_KEYWORDS = [
    "요약", "정리", "보고서", "브리핑", "리포트", "분석", "현황", "내역",
    "일지", "이력", "통계", "전체", "일주일", "한 달", "월간", "주간",
]

ERROR_KEYWORDS = [
    "망가", "고장", "오류", "에러", "작동 안", "안 나와", "안 돼", "끊겼",
    "노이즈", "흐릿", "멈춰", "재부팅", "연결", "저장 안", "녹화 안",
]


class NLPService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[Warning] OPENAI_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key)

        # KoELECTRA 의도 분류기 초기화 (선택적)
        self._koelectra = None
        if _HAS_KOELECTRA:
            try:
                clf = _IntentClassifier()
                model_path = os.path.join(_project_root, "model", "koelectra_finetuned")
                if os.path.exists(model_path):
                    clf.load_model(model_path)
                    print(f"[NLP] KoELECTRA 학습 모델 로드 완료: {model_path}")
                else:
                    print("[NLP] KoELECTRA 기본(사전학습) 모델 사용 중.")
                self._koelectra = clf
            except Exception as e:
                print(f"[NLP] KoELECTRA 로드 실패 (규칙 기반으로 대체): {e}")

        print("[Service] OpenAI NLP 서비스 초기화 완료!")

    # ── 키워드 감지 헬퍼 ──────────────────────────────────────────────
    def has_time_keyword(self, text: str) -> bool:
        return any(kw in text for kw in TIME_KEYWORDS)

    def has_person_keyword(self, text: str) -> bool:
        return any(kw in text for kw in PERSON_KEYWORDS)

    def has_count_keyword(self, text: str) -> bool:
        return any(kw in text for kw in COUNT_KEYWORDS)

    def has_action_keyword(self, text: str) -> bool:
        return any(kw in text for kw in ACTION_KEYWORDS)

    def has_summary_keyword(self, text: str) -> bool:
        return any(kw in text for kw in SUMMARY_KEYWORDS)

    def has_error_keyword(self, text: str) -> bool:
        return any(kw in text for kw in ERROR_KEYWORDS)

    # ── 문장 교정 (KoBART) ───────────────────────────────────────────
    def correct_query(self, text: str) -> str:
        """KoBART로 STT 오류를 교정합니다. 모델이 없으면 원문 반환."""
        if not _HAS_KOBART:
            return text
        try:
            return _correct_stt_text(text)
        except Exception as e:
            print(f"[NLP] 문장 교정 실패 (원문 사용): {e}")
            return text

    # ── 관점별 질문 재작성 (GPT) ─────────────────────────────────────
    def rewrite_from_perspectives(self, text: str) -> dict:
        """질문을 경비원/등장인물/행동/시간 관점으로 재작성합니다.
        키워드에 따라 포함할 관점을 동적으로 결정합니다.
        """
        include_time = self.has_time_keyword(text)
        include_person = self.has_person_keyword(text)

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

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            elif raw.startswith("```"):
                raw = raw[3:-3].strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[NLP] 관점 재작성 실패 (원문 사용): {e}")
            return {"경비원": text}

    # ── KoELECTRA 관점별 의도 분류 ───────────────────────────────────
    def _classify_perspectives_koelectra(self, perspectives: dict) -> dict:
        """각 관점 텍스트에 KoELECTRA 의도 분류를 적용합니다.
        가장 높은 confidence의 관점 텍스트와 의도를 반환합니다.
        """
        best_query = list(perspectives.values())[0]
        best_label = "unknown"
        best_confidence = -1.0
        best_perspective = list(perspectives.keys())[0]

        for label, text in perspectives.items():
            result = self._koelectra.predict(text)
            if result["confidence"] > best_confidence:
                best_confidence = result["confidence"]
                best_label = result["intent_label"]
                best_query = text
                best_perspective = label

        return {
            "best_query": best_query,
            "best_perspective": best_perspective,
            "intent_label": best_label,
            "confidence": best_confidence,
        }

    # ── 전처리 파이프라인 (메인 진입점) ──────────────────────────────
    def preprocess_query(self, text: str) -> dict:
        """
        질문 전처리 풀 파이프라인:
        1. KoBART 문장 교정
        2. 관점별 질문 재작성 (경비원/등장인물/행동/시간)
        3. KoELECTRA 의도 분류 → 가장 신뢰도 높은 관점 선택

        Returns:
            corrected      : 교정된 원문
            perspectives   : 관점별 재작성 결과 dict
            best_query     : 검색에 사용할 최적 쿼리
            best_perspective: 선택된 관점 이름
            intent_label   : 감지된 의도 (KoELECTRA) 또는 규칙 기반 추정
            confidence     : 의도 분류 신뢰도
        """
        # Step 1: 문장 교정
        corrected = self.correct_query(text)

        # Step 2: 관점별 재작성
        perspectives = self.rewrite_from_perspectives(corrected)

        # Step 3: 의도 분류 → 최적 쿼리 선택
        if self._koelectra:
            classify_result = self._classify_perspectives_koelectra(perspectives)
        else:
            # KoELECTRA 없으면 키워드로 의도 추정, 경비원 관점 기본 사용
            intent_label = self._keyword_intent_estimate(corrected)
            classify_result = {
                "best_query": perspectives.get("경비원", corrected),
                "best_perspective": "경비원",
                "intent_label": intent_label,
                "confidence": 0.5,
            }

        return {
            "corrected": corrected,
            "perspectives": perspectives,
            "best_query": classify_result["best_query"],
            "best_perspective": classify_result["best_perspective"],
            "intent_label": classify_result["intent_label"],
            "confidence": classify_result["confidence"],
        }

    def _keyword_intent_estimate(self, text: str) -> str:
        """KoELECTRA 없을 때 키워드로 의도를 간단히 추정합니다."""
        if self.has_error_keyword(text):
            return "오류 감지"
        if self.has_summary_keyword(text):
            return "정보 요약"
        if self.has_count_keyword(text):
            return "사람 수"
        if self.has_action_keyword(text):
            return "행동"
        if self.has_time_keyword(text):
            return "시간"
        return "정보 요약"

    # ── 기존 메서드 (유지) ────────────────────────────────────────────
    def generate_security_report(self, query: str, contexts: list):
        """검색된 장면들(contexts)을 바탕으로 자연어 보안 보고서를 생성합니다."""
        if not contexts:
            return "검색된 관련 데이터가 없어 보고서를 생성할 수 없습니다."

        context_text = "\n".join([f"- {c.get('description', '설명 없음')}" for c in contexts])

        system_prompt = "당신은 지능형 CCTV 보안 관제 시스템 '서치라이트'의 AI 요원입니다."
        user_prompt = f"""
사용자의 질문과 검색된 CCTV 장면 묘사들을 바탕으로 전문적인 '보안 상황 요약 보고서'를 작성해 주세요.

[사용자 질문]: {query}

[검색된 CCTV 장면 묘사들]:
{context_text}

[작성 지침]:
1. 전문 보안 요원처럼 격식 있고 명확한 문체를 사용하세요.
2. 검색된 사실(장면 묘사)에 기반하여 상황을 요약하세요.
3. 발견된 인물이나 차량의 특징, 행동을 구체적으로 언급하세요.
4. 상황의 위험성이나 특이사항이 있다면 강조해 주세요.
5. 보고서 형식으로 작성하고, 마지막은 "이상입니다."로 마무리하세요.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[NLP Error] 보고서 생성 실패: {e}")
            return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"

    def generate_ood_response(self, user_query: str):
        """보안과 관련 없는 질문(Out-of-Distribution)에 대해 친절하게 거절하는 답변을 생성합니다."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 SearchLight라는 지능형 CCTV 보안 AI야. 사용자로부터 보안과 관련 없는 일상적인 질문(인사, 날씨, 농담 등)을 받으면, 자신을 보안 전문가로 소개하며 보안 및 관제 관련 질문을 해달라고 친절하고 정중하게 요청해줘. 답변은 2문장 내외로 짧게 해."},
                    {"role": "user", "content": f"사용자 질문: {user_query}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "안녕하세요. 저는 지능형 보안 AI SearchLight입니다. 현재는 보안 및 CCTV 관제와 관련된 질문에 대해서만 도움을 드릴 수 있습니다. 궁금하신 보안 사항이 있다면 말씀해 주세요."


# 싱글톤 인스턴스 생성
nlp_service = NLPService()
