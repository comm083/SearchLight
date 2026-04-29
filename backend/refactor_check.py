import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

passed = 0
failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"[PASS] {label}")
        passed += 1
    else:
        print(f"[FAIL] {label}")
        failed += 1

print("=" * 55)
print("  SearchLight 전체 리팩토링 검증 리포트")
print("=" * 55)

# ── 1. 백엔드 구조 ─────────────────────────────────────
print("\n[1단계] 백엔드 구조 최적화")

with open("app/main.py", encoding="utf-8") as f:
    main_lines = len(f.readlines())
check(f"main.py 슬림화 ({main_lines}줄, 목표 < 60줄)", main_lines < 60)

for fname in ["app/api/__init__.py", "app/api/search.py",
              "app/api/history.py",  "app/api/alerts.py",
              "app/config.py"]:
    check(f"{fname} 파일 존재", os.path.exists(fname))

# ── 라우터 등록 검증 ───────────────────────────────────
try:
    from app.main import app
    route_paths = [r.path for r in app.routes]
    check("/api/search 라우트 등록",        "/api/search"              in route_paths)
    check("/api/search/image 라우트 등록",   "/api/search/image"        in route_paths)
    check("/api/history 라우트 등록",        "/api/history/{session_id}" in route_paths)
    check("/api/alerts 라우트 등록",         "/api/alerts/latest"       in route_paths)
except Exception as e:
    print(f"[FAIL] FastAPI 앱 로드 오류: {e}")
    failed += 1

# ── 2. 프론트엔드 컴포넌트 구조 ───────────────────────
print("\n[2단계] 프론트엔드 컴포넌트 분리")

fe_base = os.path.join("..", "frontend", "src")
new_files = [
    "hooks/useAuth.js", "hooks/useChat.js",
    "components/ChatSidebar.jsx", "components/ChatArea.jsx",
    "components/AuthModals.jsx",  "components/SettingsModal.jsx",
]
deleted_files = [
    "components/ChatInterface.jsx",
    "components/EventList.jsx",
    "components/VideoPlayer.jsx",
]

for fname in new_files:
    check(f"{fname} 생성됨", os.path.exists(os.path.join(fe_base, fname)))
for fname in deleted_files:
    check(f"{fname} 삭제됨", not os.path.exists(os.path.join(fe_base, fname)))

# App.jsx 슬림화
with open(os.path.join(fe_base, "App.jsx"), encoding="utf-8") as f:
    app_lines = len(f.readlines())
check(f"App.jsx 슬림화 ({app_lines}줄, 목표 < 130줄)", app_lines < 130)

# ── 3. AI 모듈 타입 힌팅 ───────────────────────────────
print("\n[3단계] AI 모듈 정리")

with open("../ai/intent_classifier/classifier.py", encoding="utf-8") as f:
    clf_content = f.read()
check("classifier.py  typing 임포트", "from typing import" in clf_content)
check("classifier.py  List 힌팅",     "List[str]" in clf_content)
check("classifier.py  Dict 힌팅",     "Dict[str, Any]" in clf_content)

with open("makeData/makeJsonData.py", encoding="utf-8") as f:
    mjd_content = f.read()
check("makeJsonData.py  typing 임포트", "from typing import" in mjd_content)
check("makeJsonData.py  Optional 힌팅", "Optional" in mjd_content)
check("makeJsonData.py  tuple 힌팅",    "-> tuple" in mjd_content)

with open("../ai/intent_classifier/evaluate_current_model.py", encoding="utf-8") as f:
    ev_content = f.read()
check("evaluate_current_model.py 영어 라벨 제거", "COUNTING" not in ev_content)
check("evaluate_current_model.py 한글 라벨 적용", '"사람 수"' in ev_content)

# ── 4. 삭제된 불필요 파일 ─────────────────────────────
print("\n[정리] 불필요 파일 제거")
check("test_verification.py 삭제됨", not os.path.exists("test_verification.py"))

# ── 결과 ──────────────────────────────────────────────
print()
print("=" * 55)
print(f"  총 {passed + failed}개 항목  |  통과: {passed}  |  실패: {failed}")
print("=" * 55)
