from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 서비스 모듈들 임포트 (통합)
from app.services.vector_search import faiss_service
from app.services.intent_classifier import intent_service
from app.services.database import db_service

app = FastAPI(title="SearchLight CCTV 통합 검색 API", version="2.0")

# CORS 설정 (프론트엔드의 접근을 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 보안상 나중엔 실제 프론트엔드 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 2

@app.post("/api/search")
async def process_user_query(request: SearchRequest):
    query_text = request.query
    
    # 1. 의도 분류 (KoELECTRA)
    intent_result = intent_service.classify(query_text)
    current_intent = intent_result["intent"]
    
    # 2. 로그 기록 (SQLite) - 사용자가 무슨 검색을 했는지 저장
    db_service.log_search(query=query_text, intent=current_intent)
    
    # 3. 라우팅 로직 (검색 의도일 경우에만 FAISS 접근)
    if current_intent == "SEARCH":
        # 4. 벡터 검색 수행 (FAISS)
        search_results = faiss_service.search(query=query_text, top_k=request.top_k)
        
        return {
            "status": "success",
            "message": "CCTV 영상 검색을 완료했습니다.",
            "intent_info": intent_result,
            "results": search_results
        }
    else:
        # 검색 의도가 아닐 경우 바로 차단/안내
        return {
            "status": "blocked",
            "message": "검색과 관련된 요청이 아닙니다. 정확한 인상착의나 상황을 입력해주세요.",
            "intent_info": intent_result,
            "results": []
        }

if __name__ == "__main__":
    import uvicorn
    # app/ 폴더 외부(backend)에서 uvicorn을 실행해야 모듈 임포트가 정상 작동합니다.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
