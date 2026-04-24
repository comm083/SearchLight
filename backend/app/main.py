from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# 서비스 모듈들 임포트 (통합)
from app.services.vector_search import faiss_service
from app.services.intent_classifier import intent_service
from app.services.database import db_service
from app.services.time_parser import parse_time_expression

app = FastAPI(title="SearchLight CCTV 통합 검색 API", version="2.0")

# 정적 파일(이미지) 서빙 설정
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS 설정 (프론트엔드의 접근을 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 2

# 5가지 의도별 맞춤 응답 메시지
INTENT_MESSAGES = {
    "SEARCH":    "CCTV 영상 검색을 완료했습니다.",
    "EMERGENCY": "🚨 긴급 상황이 감지되었습니다. 즉시 관계자에게 연락하고 해당 구역을 확인해 주세요.",
    "ERROR":     "⚠️ 시스템 장애 관련 문의입니다. 카메라 연결 상태 및 네트워크를 점검해 주세요.",
    "ACCESS":    "🚗 출입 기록을 검색합니다.",
    "GENERAL":   "💬 일반 대화로 분류되었습니다. CCTV 검색을 원하시면 구체적인 상황이나 인상착의를 입력해 주세요.",
}

@app.post("/api/search")
async def process_user_query(request: SearchRequest):
    query_text = request.query

    # 1. 의도 분류 (KoELECTRA - 5종)
    intent_result = intent_service.classify(query_text)
    current_intent = intent_result["intent"]

    # 2. 시간 표현 파싱
    time_info = parse_time_expression(query_text)

    # 3. 로그 기록 (Supabase)
    db_service.log_search(query=query_text, intent=current_intent)

    # 4. 의도별 라우팅
    if current_intent in ("SEARCH", "ACCESS"):
        # 벡터 검색 수행 (FAISS)
        search_results = faiss_service.search(query=query_text, top_k=request.top_k)
        return {
            "status": "success",
            "message": INTENT_MESSAGES[current_intent],
            "intent_info": intent_result,
            "time_info": time_info,
            "results": search_results
        }
    elif current_intent == "EMERGENCY":
        return {
            "status": "emergency",
            "message": INTENT_MESSAGES["EMERGENCY"],
            "intent_info": intent_result,
            "time_info": time_info,
            "results": []
        }
    elif current_intent == "ERROR":
        return {
            "status": "error_report",
            "message": INTENT_MESSAGES["ERROR"],
            "intent_info": intent_result,
            "time_info": time_info,
            "results": []
        }
    else:
        return {
            "status": "blocked",
            "message": INTENT_MESSAGES["GENERAL"],
            "intent_info": intent_result,
            "time_info": time_info,
            "results": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
