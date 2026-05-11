"""
SearchLight - Search Accuracy Evaluation
=========================================
Intent classifier and vector search accuracy measurement.

Usage:
  python makeData/evaluate_search.py                   # all (default)
  python makeData/evaluate_search.py --mode intent     # intent only
  python makeData/evaluate_search.py --mode retrieval  # retrieval only
  python makeData/evaluate_search.py --mode show-db    # DB 이벤트 목록 출력
  python makeData/evaluate_search.py --top_k 5

expected_keywords  : 결과 summary에 반드시 포함되어야 할 텍스트 키워드 리스트
expected_situation : 결과 situation 태그가 일치해야 함 (assault/break/falling/smoking/theft)
  - 둘 다 None  → 검색 응답률/유사도만 측정
  - 둘 중 하나만 있어도 Hit 판정
"""

import os
import sys
import argparse
from collections import defaultdict

# Windows UTF-8 출력 강제
if os.environ.get("PYTHONUTF8") != "1":
    os.environ["PYTHONUTF8"] = "1"
    os.execv(sys.executable, [sys.executable] + sys.argv)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 경로 설정
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_PROJECT = os.path.abspath(os.path.join(_BACKEND, ".."))
sys.path.insert(0, _BACKEND)
sys.path.insert(0, _PROJECT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_BACKEND, ".env"))


# ======================================================================
# 테스트 데이터셋
#
# expected_intent    : 정답 의도 레이블
# expected_keywords  : 결과 summary에 포함되어야 할 키워드 (리스트)
# expected_situation : 결과 situation 태그 (assault / break / falling / smoking / theft)
#   → 둘 다 None이면 해당 쿼리는 검색 정확도 평가 제외
#
# DB 현황 (2026-05-11 기준):
#   assault 2건 / break 5건 / falling 2건 / smoking 3건 / theft 3건 / normal 3건
# ======================================================================
TEST_QUERIES = [
    # ── COUNTING ─────────────────────────────────────────────────────
    {"query": "오늘 몇 명이나 됐어?",            "expected_intent": "COUNTING",      "expected_keywords": None, "expected_situation": None},
    {"query": "이번 주 총 몇 명 감지됐어?",       "expected_intent": "COUNTING",      "expected_keywords": None, "expected_situation": None},
    {"query": "차량이 몇 대나 들어왔어?",         "expected_intent": "COUNTING",      "expected_keywords": None, "expected_situation": None},
    {"query": "어제 방문자 수 알려줘",            "expected_intent": "COUNTING",      "expected_keywords": None, "expected_situation": None},
    {"query": "오전에 총 몇 번 알림 울렸어?",     "expected_intent": "COUNTING",      "expected_keywords": None, "expected_situation": None},
    {"query": "이번 달 침입 횟수 집계해줘",       "expected_intent": "COUNTING",      "expected_keywords": None, "expected_situation": None},

    # ── SUMMARIZATION ────────────────────────────────────────────────
    {"query": "어제 무슨 일 있었어?",             "expected_intent": "SUMMARIZATION", "expected_keywords": None, "expected_situation": None},
    {"query": "오전 상황 요약해줘",               "expected_intent": "SUMMARIZATION", "expected_keywords": ["인물"], "expected_situation": None},
    {"query": "지난 이벤트 정리해줘",             "expected_intent": "SUMMARIZATION", "expected_keywords": ["인물"], "expected_situation": None},
    {"query": "최근 영상 보여줘",                 "expected_intent": "SUMMARIZATION", "expected_keywords": ["인물"], "expected_situation": None},
    {"query": "어떤 일들이 있었는지 알려줘",      "expected_intent": "SUMMARIZATION", "expected_keywords": None, "expected_situation": None},
    {"query": "이번 주 보안 상황 보고해줘",        "expected_intent": "SUMMARIZATION", "expected_keywords": ["인물"], "expected_situation": None},
    {"query": "저번 주 주요 이벤트 정리해줘",      "expected_intent": "SUMMARIZATION", "expected_keywords": ["인물"], "expected_situation": None},

    # ── LOCALIZATION ─────────────────────────────────────────────────
    {"query": "지금 정문에 사람 있어?",           "expected_intent": "LOCALIZATION",  "expected_keywords": None, "expected_situation": None},
    {"query": "현재 주차장 상황은?",              "expected_intent": "LOCALIZATION",  "expected_keywords": None, "expected_situation": None},
    {"query": "지금 당장 어디 있어?",             "expected_intent": "LOCALIZATION",  "expected_keywords": None, "expected_situation": None},
    {"query": "실시간으로 확인해줘",              "expected_intent": "LOCALIZATION",  "expected_keywords": None, "expected_situation": None},

    # ── BEHAVIORAL ───────────────────────────────────────────────────
    {"query": "수상한 사람 없었어?",              "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": "theft"},
    {"query": "이상한 행동 감지됐어?",            "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": "assault"},
    {"query": "폭행 사건 있었어?",                "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": "assault"},
    {"query": "배회하는 사람 포착됐어?",           "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": "theft"},
    {"query": "쓰러진 사람 있었나?",              "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": "falling"},
    {"query": "화재 감지된 적 있어?",             "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": None},
    {"query": "담 넘는 거 없었어?",               "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": None},
    {"query": "절도 사건 기록 있어?",             "expected_intent": "BEHAVIORAL",    "expected_keywords": None, "expected_situation": "theft"},

    # ── CAUSAL ───────────────────────────────────────────────────────
    {"query": "왜 알림이 울렸어?",                "expected_intent": "CAUSAL",        "expected_keywords": None, "expected_situation": None},
    {"query": "그 사건 어떻게 생긴 거야?",         "expected_intent": "CAUSAL",        "expected_keywords": None, "expected_situation": "assault"},
    {"query": "이유가 뭐야?",                     "expected_intent": "CAUSAL",        "expected_keywords": None, "expected_situation": None},
    {"query": "어쩌다 그렇게 됐어?",              "expected_intent": "CAUSAL",        "expected_keywords": None, "expected_situation": None},
    {"query": "사고 경위를 설명해줘",             "expected_intent": "CAUSAL",        "expected_keywords": None, "expected_situation": "falling"},
]

INTENT_LABELS = ["COUNTING", "SUMMARIZATION", "LOCALIZATION", "BEHAVIORAL", "CAUSAL", "CHITCHAT"]

GRADE = [(100, "완벽"), (80, "양호"), (50, "보통"), (20, "취약"), (0, "매우 취약")]

def _grade(pct):
    for threshold, label in GRADE:
        if pct >= threshold:
            return label
    return "매우 취약"

def _summary_bar(correct, total, bar_width=8):
    pct = correct / total * 100 if total else 0
    filled = round(pct / 100 * bar_width)
    bar = "#" * filled + "-" * (bar_width - filled)
    return pct, bar

def _print_grade_table(rows, title="Overall accuracy"):
    """rows: list of (label, correct, total)"""
    total_c = sum(r[1] for r in rows)
    total_t = sum(r[2] for r in rows)
    total_pct = total_c / total_t * 100 if total_t else 0
    print(f"\n{title}: {total_c}/{total_t} ({total_pct:.1f}%)\n")
    rows_sorted = sorted(rows, key=lambda x: -(x[1] / x[2]) if x[2] else 0)
    for label, c, t in rows_sorted:
        if t == 0:
            continue
        pct, bar = _summary_bar(c, t)
        grade = _grade(pct)
        print(f"{label:<14}: {c}/{t}  ({pct:3.0f}%)  [{bar}]   {grade}")


# ======================================================================
# DB 이벤트 목록 출력
# ======================================================================
def show_db():
    from app.services.vector_db_service import vector_db_service
    events = vector_db_service.scene_data
    print(f"\n{'='*70}")
    print(f"  DB 이벤트 목록 ({len(events)}개)")
    print(f"{'='*70}")
    print(f"{'#':>3}  {'situation':<12} {'date':<17} summary (앞 60자)")
    print("-"*70)
    for i, e in enumerate(events, 1):
        sit  = e.get("situation") or "normal"
        date = str(e.get("event_date") or "")[:16]
        summ = (e.get("summary") or "").replace("\n", " ")[:60]
        print(f"{i:>3}. [{sit:<10}] {date}  {summ}")
    print()
    # situation 집계
    counts = defaultdict(int)
    for e in events:
        counts[e.get("situation") or "normal"] += 1
    print("상황 분포:", "  /  ".join(f"{k} {v}건" for k, v in sorted(counts.items())))


# ======================================================================
# 의도 분류 정확도 평가
# ======================================================================
def evaluate_intent():
    from app.services.intent_classifier import intent_service

    print("\n" + "=" * 70)
    print("  Intent Classifier Accuracy")
    print("=" * 70)
    print(f"{'Query':<35} {'Expected':^14} {'Predicted':^14} {'Conf':>5}")
    print("-" * 70)

    correct = 0
    total = len(TEST_QUERIES)
    per_intent_correct = defaultdict(int)
    per_intent_total   = defaultdict(int)
    misclassified = []
    confusion = defaultdict(lambda: defaultdict(int))

    for item in TEST_QUERIES:
        query    = item["query"]
        expected = item["expected_intent"]
        result   = intent_service.classify(query)
        predicted, conf = result.intent, result.confidence

        per_intent_total[expected] += 1
        confusion[expected][predicted] += 1

        is_correct = predicted == expected
        if is_correct:
            correct += 1
            per_intent_correct[expected] += 1
        else:
            misclassified.append({"query": query, "expected": expected,
                                   "predicted": predicted, "confidence": conf})

        mark    = "O" if is_correct else "X"
        q_short = query[:32] + ".." if len(query) > 32 else query
        print(f"[{mark}] {q_short:<33} {expected:^14} {predicted:^14} {conf:>4.0%}")

    print("=" * 70)

    if misclassified:
        print(f"\n-- 오분류 ({len(misclassified)}건) " + "-" * 50)
        for m in misclassified:
            print(f'  "{m["query"]}"')
            print(f'    정답 {m["expected"]}  ->  예측 {m["predicted"]} ({m["confidence"]:.0%})')

    # 혼동 행렬
    active = [i for i in INTENT_LABELS if per_intent_total.get(i, 0) > 0]
    print("\n-- Confusion matrix (행=정답, 열=예측) " + "-" * 25)
    print(f"{'':^16}" + "".join(f"{i:^16}" for i in active))
    for ti in active:
        row = f"{ti:^16}"
        for pi in active:
            v = confusion[ti][pi]
            cell = f"[{v}]" if ti == pi else (str(v) if v else ".")
            row += f"{cell:^16}"
        print(row)

    rows = [(intent, per_intent_correct.get(intent, 0), per_intent_total.get(intent, 0))
            for intent in INTENT_LABELS if per_intent_total.get(intent, 0) > 0]
    _print_grade_table(rows, title="Overall accuracy")

    return correct / total * 100, misclassified


# ======================================================================
# 벡터 검색 정확도 평가
# ======================================================================
def _is_hit(result: dict, expected_keywords, expected_situation) -> bool:
    """결과 1건이 기대값(keywords 또는 situation)을 만족하는지 확인"""
    if expected_keywords:
        summary = (result.get("description") or result.get("summary") or "").lower()
        if all(kw.lower() in summary for kw in expected_keywords):
            return True
    if expected_situation:
        if result.get("situation") == expected_situation:
            return True
    return False


def evaluate_retrieval(top_k: int = 3, threshold: float = 0.25):
    from app.services.vector_db_service import vector_db_service

    labeled = [q for q in TEST_QUERIES
               if q.get("expected_keywords") or q.get("expected_situation")]

    print(f"\n{'='*70}")
    print(f"  Vector Search Accuracy (Top-{top_k}, threshold={threshold})")
    print(f"  ※ 운영 임계값 0.35 기준 평가 시 --threshold 0.35 옵션 사용")
    print(f"{'='*70}")

    if not labeled:
        print("\n[INFO] expected_keywords / expected_situation 설정된 쿼리 없음")
        print("       --mode show-db 로 DB 확인 후 TEST_QUERIES에 기준을 설정하세요.\n")
        print("-- 대신: 응답률 / 평균 유사도 측정 " + "-" * 30)
        _response_rate(vector_db_service, top_k)
        return None

    hit_at_1 = hit_at_k = 0
    mrr_sum   = 0.0
    total     = len(labeled)
    per_intent = defaultdict(lambda: {"hit": 0, "total": 0})

    print(f"{'Query':<35} {'기준':^12} {'Hit':^8} Top-{top_k} scores")
    print("-" * 70)

    for item in labeled:
        query    = item["query"]
        intent   = item["expected_intent"]
        ekw      = item.get("expected_keywords")
        esit     = item.get("expected_situation")
        results  = vector_db_service.search(query=query, top_k=top_k, threshold=threshold)

        hit_rank = None
        for rank, r in enumerate(results, start=1):
            if _is_hit(r, ekw, esit):
                hit_rank = rank
                break

        per_intent[intent]["total"] += 1
        if hit_rank == 1:
            hit_at_1 += 1
        if hit_rank is not None:
            hit_at_k += 1
            mrr_sum += 1.0 / hit_rank
            per_intent[intent]["hit"] += 1

        # 기준 표시
        criterion = f"sit={esit}" if esit else f'"{ekw[0]}"' if ekw else "?"
        mark   = f"Hit@{hit_rank}" if hit_rank else "Miss"
        scores = [round(r.get("score", 0), 3) for r in results[:top_k]]
        q_short = query[:32] + ".." if len(query) > 32 else query
        print(f"[{mark:^6}] {q_short:<33} {criterion:<12} {scores}")

    print("=" * 70)
    overall_pct = hit_at_k / total * 100
    print(f"\nHit@1  : {hit_at_1}/{total} ({hit_at_1/total*100:.1f}%)")
    print(f"Hit@{top_k}  : {hit_at_k}/{total} ({overall_pct:.1f}%)")
    print(f"MRR    : {mrr_sum/total:.3f}")

    # per-intent 요약 (같은 grade 형식)
    rows = [(intent, d["hit"], d["total"]) for intent, d in per_intent.items()]
    _print_grade_table(rows, title=f"Retrieval Hit@{top_k}")

    return {"hit_at_1": hit_at_1/total, f"hit_at_{top_k}": hit_at_k/total, "mrr": mrr_sum/total}


def _response_rate(vector_db_service, top_k: int):
    print(f"{'Query':<35} {'#':^4} {'AvgScore':>8}  Top-1 situation")
    print("-" * 65)
    total = len(TEST_QUERIES)
    responded = 0
    per_intent = defaultdict(list)

    for item in TEST_QUERIES:
        results = vector_db_service.search(query=item["query"], top_k=top_k)
        cnt  = len(results)
        avg  = sum(r.get("score", 0) for r in results) / cnt if cnt else 0.0
        sit1 = results[0].get("situation", "-") if results else "-"
        if cnt: responded += 1
        per_intent[item["expected_intent"]].append(avg)
        q_short = item["query"][:32] + ".." if len(item["query"]) > 32 else item["query"]
        print(f"  {q_short:<33} {cnt:^4} {avg:>8.3f}  [{sit1}]")

    print("=" * 65)
    print(f"응답률: {responded}/{total} ({responded/total*100:.1f}%)")
    print("\n-- 의도별 평균 유사도 " + "-" * 40)
    for intent in INTENT_LABELS:
        scores = per_intent.get(intent, [])
        if not scores: continue
        avg = sum(scores) / len(scores)
        bar = "#" * int(avg * 20)
        print(f"  {intent:<14}: {avg:.3f}  [{bar:<20}]")


# ======================================================================
# Entry point
# ======================================================================
def main():
    parser = argparse.ArgumentParser(description="SearchLight accuracy evaluation")
    parser.add_argument("--mode",  choices=["intent", "retrieval", "all", "show-db"],
                        default="all")
    parser.add_argument("--top_k",     type=int,   default=3)
    parser.add_argument("--threshold", type=float, default=0.25,
                        help="검색 유사도 임계값 (기본 0.25 / 운영: 0.35)")
    args = parser.parse_args()

    if args.mode == "show-db":
        show_db()
        return

    if args.mode in ("intent", "all"):
        evaluate_intent()

    if args.mode in ("retrieval", "all"):
        evaluate_retrieval(top_k=args.top_k, threshold=args.threshold)

    print("\n평가 완료.")


if __name__ == "__main__":
    main()
