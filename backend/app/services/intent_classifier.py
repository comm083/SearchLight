"""
보안 관제 의도 분류기 (Intent Classifier)
===========================================
두 가지 구현 방식을 모두 제공합니다:

[방식 A] 규칙 기반 (즉시 실행 가능, 파인튜닝 불필요)
  - 키워드 매칭 + 가중치 점수 계산
  - 장점: 라이브러리 없음, 즉시 동작
  - 단점: 신조어/비유적 표현에 취약

[방식 B] KoELECTRA 파인튜닝 (권장 최종 버전)
  - transformers + 학습 데이터 필요
  - 장점: 문맥 이해, 높은 정확도
  - 단점: GPU/학습 시간 필요

의도 분류 5종:
  COUNTING       "몇 명이야?" → SQLite COUNT 쿼리
  SUMMARIZATION  "무슨 일 있었어?" → Vector RAG 검색
  LOCALIZATION   "지금 어디 있어?" → SQLite 최신 기록
  BEHAVIORAL     "수상한 거 없었어?" → 이벤트 레코드 + RAG
  CAUSAL         "왜 알림이 울렸어?" → SQLite + RAG 결합
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re


# ─── 결과 데이터 클래스 ──────────────────────────────────────────────
@dataclass
class IntentResult:
    intent: str           # 최종 분류 클래스
    confidence: float     # 0.0 ~ 1.0
    scores: dict          # 각 클래스별 점수 (디버깅용)
    db_route: str         # 어떤 DB를 조회할지
    method: str           # "rule_based" or "koelectra"

    # DB 라우팅 설명
    ROUTE_DESC = {
        "sqlite_count":    "SQLite COUNT 쿼리 → 숫자 답변",
        "sqlite_latest":   "SQLite 최신 레코드 → 현재 상태 답변",
        "vector_rag":      "FAISS 벡터 검색 → LLM 요약 답변",
        "event_rag":       "이벤트 필터 + FAISS → 이상 행동 답변",
        "sqlite_and_rag":  "SQLite + FAISS 결합 → LLM 인과 분석",
    }

    def __str__(self):
        route_desc = self.ROUTE_DESC.get(self.db_route, self.db_route)
        top3 = sorted(self.scores.items(), key=lambda x: -x[1])[:3]
        score_str = "  |  ".join(f"{k}:{v:.2f}" for k, v in top3)
        return (f"의도: {self.intent:<18} 신뢰도: {self.confidence:.0%}\n"
                f"   라우팅: {route_desc}\n"
                f"   점수: {score_str}")


# ─────────────────────────────────────────────────────────────────────
# 방식 A: 규칙 기반 분류기
# ─────────────────────────────────────────────────────────────────────
class RuleBasedIntentClassifier:
    """
    키워드 패턴 + 가중치 점수로 의도를 분류합니다.
    학습 데이터나 GPU 없이 즉시 동작합니다.
    """

    # 각 의도별 키워드와 가중치 (높을수록 강한 신호)
    PATTERNS = {
        "COUNTING": {
            "keywords": [
                ("몇 명", 3.0), ("몇명", 3.0), ("몇 대", 3.0), ("몇대", 3.0),
                ("총 몇", 2.5), ("몇 번", 2.0), ("몇번", 2.0), ("횟수", 2.0),
                ("카운트", 1.5), ("합계", 1.5), ("총", 1.0), ("집계", 2.0),
                ("몇 회", 2.0), ("몇 개", 1.5), ("통계", 1.5),
            ],
            "regex": [r"몇\s*(명|대|번|회|개|차례)"],
            "db_route": "sqlite_count",
        },
        "SUMMARIZATION": {
            "keywords": [
                ("무슨 일", 3.0), ("뭔 일", 2.5), ("어땠어", 2.5),
                ("요약", 3.0), ("정리", 2.5), ("알려줘", 1.5),
                ("보고", 2.0), ("상황", 1.5), ("어떻게 됐", 2.0),
                ("있었어", 1.5), ("무슨", 1.0), ("내용", 1.5),
            ],
            "regex": [r"(어떤|무슨|뭔).*(있|있었|있나|있어)"],
            "db_route": "vector_rag",
        },
        "LOCALIZATION": {
            "keywords": [
                ("지금", 3.0), ("현재", 3.0), ("있어?", 2.5), ("있나?", 2.5),
                ("어디", 2.0), ("위치", 2.5), ("있는지", 2.0),
                ("실시간", 2.5), ("방금", 1.5), ("지금 당장", 3.0),
            ],
            "regex": [
                r"(지금|현재).*(있|없|어디)",
                r"(어디에|어디서).*(있|없)",
            ],
            "db_route": "sqlite_latest",
        },
        "BEHAVIORAL": {
            "keywords": [
                ("수상", 3.0), ("이상", 2.5), ("의심", 3.0),
                ("배회", 3.0), ("서성", 3.0), ("침입", 3.0),
                ("낯선", 2.5), ("이상한", 2.5), ("특이", 2.0),
                ("이상 행동", 3.0), ("위험", 2.5), ("위협", 3.0),
                ("몰래", 2.5), ("숨어", 2.5), ("빠져나", 2.5),
                ("담 넘", 3.0), ("무단", 2.5), ("불법", 2.0),
                ("불", 3.0), ("방화", 3.0), ("화재", 3.0), ("연기", 2.5),
                ("싸움", 3.0), ("폭행", 3.0), ("때림", 2.5), ("멱살", 2.5),
                ("절도", 3.0), ("훔침", 3.0), ("몰래 넣", 3.0),
            ],
            "regex": [
                r"(수상|의심|이상한|낯선).*(사람|인물|남자|여자|차)",
                r"(침입|무단|불법).*(했|있|됐|감지)",
            ],
            "db_route": "event_rag",
        },
        "CAUSAL": {
            "keywords": [
                ("왜", 3.0), ("이유", 3.0), ("원인", 3.0),
                ("어떻게 된", 2.5), ("어째서", 2.5),
                ("어떻게 발생", 2.5), ("경위", 3.0),
                ("어떻게 생긴", 2.5), ("어쩌다", 2.0),
                ("설명해", 2.0), ("설명해줘", 2.5), ("분석", 2.0),
            ],
            "regex": [
                r"왜\s.*(울|났|발생|생긴|됐)",
                r"(어떻게|어째서)\s.*(됐|생긴|발생)",
            ],
            "db_route": "sqlite_and_rag",
        },
        "CHITCHAT": {
            "keywords": [
                ("안녕", 3.0), ("반가워", 3.0), ("하이", 3.0), ("헬로", 3.0),
                ("뭐해", 2.5), ("배고파", 2.5), ("졸려", 2.0), ("심심", 2.0),
                ("날씨", 3.0), ("오늘 기분", 2.5), ("누구야", 2.0), ("이름", 2.0),
                ("고마워", 2.0), ("잘가", 2.0), ("바보", 3.0), ("사랑해", 2.0),
            ],
            "regex": [
                r"(안녕|하이|방가).*",
                r".*(뭐해|누구야|뭐니).*",
                r".*(날씨|기분|배고|졸려).*",
            ],
            "db_route": "none",
        },
    }

    # DB 라우팅 매핑
    ROUTE_MAP = {
        "COUNTING":      "sqlite_count",
        "SUMMARIZATION": "vector_rag",
        "LOCALIZATION":  "sqlite_latest",
        "BEHAVIORAL":    "event_rag",
        "CAUSAL":        "sqlite_and_rag",
        "CHITCHAT":      "none",
    }

    def classify(self, query: str) -> IntentResult:
        scores = {intent: 0.0 for intent in self.PATTERNS}

        for intent, config in self.PATTERNS.items():
            # 키워드 점수
            for keyword, weight in config["keywords"]:
                if keyword in query:
                    scores[intent] += weight

            # 정규식 패턴 점수 (더 강한 신호)
            for pattern in config.get("regex", []):
                if re.search(pattern, query):
                    scores[intent] += 2.0

        total = sum(scores.values())
        if total == 0:
            # 점수가 0이면 SUMMARIZATION 기본값
            return IntentResult(
                intent="SUMMARIZATION", confidence=0.4,
                scores=scores, db_route="vector_rag",
                method="rule_based:fallback"
            )

        # softmax-like 정규화
        norm_scores = {k: v / total for k, v in scores.items()}
        best_intent = max(norm_scores, key=norm_scores.get)
        confidence  = norm_scores[best_intent]

        # 신뢰도가 너무 낮으면 SUMMARIZATION 기본값
        if confidence < 0.35:
            best_intent = "SUMMARIZATION"
            confidence  = 0.40

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            scores=norm_scores,
            db_route=self.ROUTE_MAP[best_intent],
            method="rule_based"
        )


# ─────────────────────────────────────────────────────────────────────
# 방식 B: KoELECTRA 파인튜닝 코드 (설치 후 실행)
# ─────────────────────────────────────────────────────────────────────
KOELECTRA_TRAIN_CODE = '''
# ─── 파인튜닝 실행 코드 (torch + transformers 설치 필요) ────────────

from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                           Trainer, TrainingArguments)
from torch.utils.data import Dataset
import torch, json

MODEL_NAME = "monologg/koelectra-base-v3-discriminator"
LABELS = ["COUNTING", "SUMMARIZATION", "LOCALIZATION", "BEHAVIORAL", "CAUSAL"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}

# ── 데이터셋 클래스 ─────────────────────────────────────────────────
class IntentDataset(Dataset):
    def __init__(self, data, tokenizer, max_len=128):
        self.encodings = tokenizer(
            [d["query"] for d in data],
            truncation=True, padding=True, max_length=max_len,
            return_tensors="pt"
        )
        self.labels = torch.tensor([LABEL2ID[d["intent"]] for d in data])

    def __len__(self):  return len(self.labels)
    def __getitem__(self, i):
        return {k: v[i] for k, v in self.encodings.items()} | \
               {"labels": self.labels[i]}

# ── 학습 데이터 예시 (300건 이상 권장) ─────────────────────────────
train_data = [
    {"query": "오늘 몇 명 왔어?",          "intent": "COUNTING"},
    {"query": "이번 주 차량 대수 알려줘",   "intent": "COUNTING"},
    {"query": "오전에 총 몇 번 감지됐어?",  "intent": "COUNTING"},
    {"query": "방문객 집계 해줘",           "intent": "COUNTING"},

    {"query": "어제 오후에 무슨 일 있었어?","intent": "SUMMARIZATION"},
    {"query": "교대 시간대 정리해줘",       "intent": "SUMMARIZATION"},
    {"query": "오전 상황 요약해줘",         "intent": "SUMMARIZATION"},
    {"query": "지난 1시간 보고해줘",        "intent": "SUMMARIZATION"},

    {"query": "지금 정문에 사람 있어?",     "intent": "LOCALIZATION"},
    {"query": "현재 A구역 상황은?",         "intent": "LOCALIZATION"},
    {"query": "주차장에 차 있나?",          "intent": "LOCALIZATION"},
    {"query": "지금 당장 어디 있어?",       "intent": "LOCALIZATION"},

    {"query": "수상한 사람 없었어?",        "intent": "BEHAVIORAL"},
    {"query": "이상한 행동 감지됐어?",      "intent": "BEHAVIORAL"},
    {"query": "담 넘는 사람 있었나?",       "intent": "BEHAVIORAL"},
    {"query": "배회하는 거 없었어?",        "intent": "BEHAVIORAL"},

    {"query": "왜 알림이 울렸어?",          "intent": "CAUSAL"},
    {"query": "그 사고 어떻게 생긴 거야?",  "intent": "CAUSAL"},
    {"query": "어쩌다 그렇게 됐어?",        "intent": "CAUSAL"},
    {"query": "경위를 설명해줘",            "intent": "CAUSAL"},
    # ... 총 300건 이상 작성
]

# ── 학습 실행 ───────────────────────────────────────────────────────
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=len(LABELS)
)

split = int(len(train_data) * 0.8)
train_ds = IntentDataset(train_data[:split], tokenizer)
val_ds   = IntentDataset(train_data[split:], tokenizer)

args = TrainingArguments(
    output_dir="./intent_model",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    eval_strategy="epoch",
    save_strategy="best",
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    logging_steps=10,
)
Trainer(model=model, args=args,
        train_dataset=train_ds, eval_dataset=val_ds).train()
model.save_pretrained("./intent_model_final")
tokenizer.save_pretrained("./intent_model_final")
print("학습 완료! ./intent_model_final 에 저장됨")

# ── 추론 ────────────────────────────────────────────────────────────
def classify_with_koelectra(query: str) -> dict:
    model.eval()
    inputs = tokenizer(query, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs  = torch.softmax(logits, dim=-1)[0]
    pred   = torch.argmax(probs).item()
    return {
        "intent":     LABELS[pred],
        "confidence": probs[pred].item(),
        "scores":     {l: probs[i].item() for i, l in enumerate(LABELS)},
    }
'''


# ─────────────────────────────────────────────────────────────────────
# 통합 파이프라인 데모
# ─────────────────────────────────────────────────────────────────────
def run_full_pipeline_demo():
    from korean_time_parser import KoreanTimeParser, TimeRange
    from datetime import datetime

    mock_now = datetime(2026, 4, 22, 15, 30, 0)
    time_parser = KoreanTimeParser(now=mock_now)
    intent_clf  = RuleBasedIntentClassifier()

    print("\n" + "="*68)
    print("  서치라이트 — NLP 파이프라인 통합 데모")
    print(f"  기준 시각: {mock_now.strftime('%Y-%m-%d %H:%M')}")
    print("="*68)

    queries = [
        "어제 오후 교대 시간에 A구역에 누가 있었어?",
        "오늘 정문으로 총 몇 명 들어왔어?",
        "지금 주차장에 차 있나?",
        "어제 오후 두 시에 수상한 사람 없었어?",
        "왜 30분 전에 경보가 울렸어?",
        "오늘 오전 로비 상황 요약해줘",
    ]

    # 기대 DB 라우팅 (검증용)
    expected = [
        "vector_rag",      # 교대 시간 요약
        "sqlite_count",    # 몇 명
        "sqlite_latest",   # 지금 현재
        "event_rag",       # 수상한 행동
        "sqlite_and_rag",  # 왜 (인과)
        "vector_rag",      # 요약
    ]

    passed = 0
    for i, query in enumerate(queries):
        time_result   = time_parser.parse(query)
        intent_result = intent_clf.classify(query)
        correct = intent_result.db_route == expected[i]
        if correct: passed += 1
        icon = "✅" if correct else "❌"

        print(f"\n{icon} [{i+1}] 질의: \"{query}\"")
        print(f"  ⏰ 시간 파서  : {time_result or '파싱 실패'}")
        print(f"  🧠 의도 분류 : {intent_result}")
        print(f"  🔀 DB 라우팅 : {intent_result.db_route}")

    print(f"\n{'='*68}")
    print(f"  의도 분류 정확도: {passed}/{len(queries)} ({passed/len(queries)*100:.0f}%)")
    print("="*68 + "\n")


# ─────────────────────────────────────────────────────────────────────
# 단독 테스트
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    clf = RuleBasedIntentClassifier()

    tests = [
        ("오늘 몇 명 왔어?",                    "COUNTING"),
        ("방문객 집계 해줘",                     "COUNTING"),
        ("어제 오후에 무슨 일 있었어?",           "SUMMARIZATION"),
        ("교대 시간대 정리해줘",                  "SUMMARIZATION"),
        ("지금 정문에 사람 있어?",               "LOCALIZATION"),
        ("현재 A구역 상황은?",                   "LOCALIZATION"),
        ("수상한 사람 없었어?",                   "BEHAVIORAL"),
        ("담 넘으려는 사람 감지됐어?",            "BEHAVIORAL"),
        ("왜 알림이 울렸어?",                    "CAUSAL"),
        ("그 사고 어떻게 생긴 거야?",             "CAUSAL"),
        ("어제 오후 교대 시간에 A구역에 누가 있었어?", "SUMMARIZATION"),
    ]

    print("\n" + "="*68)
    print("  규칙 기반 의도 분류기 — 단독 테스트")
    print("="*68)

    passed = 0
    for query, expected in tests:
        result = clf.classify(query)
        ok = result.intent == expected
        if ok: passed += 1
        icon = "✅" if ok else f"❌(예상:{expected})"
        print(f"\n{icon}")
        print(f"  질의: \"{query}\"")
        print(f"  {result}")

    print(f"\n{'='*68}")
    print(f"  통과: {passed}/{len(tests)} ({passed/len(tests)*100:.0f}%)")
    print("="*68 + "\n")

    # 파이프라인 통합 실행
    print("\n── 통합 파이프라인 실행 ──")
    run_full_pipeline_demo()

# 서비스 인스턴스 생성 (백엔드 통합용)
intent_service = RuleBasedIntentClassifier()
