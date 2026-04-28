from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import shutil

# 서비스 모듈들 임포트 (통합)
from app.services.vector_db_service import vector_db_service
from app.services.intent_classifier import intent_service
from app.services.database import db_service
from app.services.korean_time_parser import KoreanTimeParser
from app.services.nlp_service import nlp_service
from app.services.alert_service import alert_service
from app.services.image_search_service import image_search_service

app = FastAPI(title="SearchLight CCTV 통합 검색 API", version="2.4")

# 전역 대화 메모리 (세션별 저장)
SESSION_MEMORY = {}
time_parser = KoreanTimeParser()

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

from typing import Optional

class SearchRequest(BaseModel):
    query: str
    top_k: int = 2
    session_id: str = "default"
    start_time: Optional[str] = None
    end_time: Optional[str] = None

# 5가지 의도별 맞춤 응답 메시지
INTENT_MESSAGES = {
    "COUNTING":     "대상에 대한 수량 집계를 완료했습니다.",
    "SUMMARIZATION": "해당 시간대의 보안 상황을 요약하여 보고합니다.",
    "LOCALIZATION":  "현재 실시간 위치 및 상태를 확인합니다.",
    "BEHAVIORAL":    "이상 행동 분석 및 검색 결과를 보고합니다.",
    "CAUSAL":        "이벤트 발생 원인 및 인과 관계를 분석합니다.",
    "EMERGENCY":     "🚨 긴급 상황이 감지되었습니다. 즉시 관계자에게 연락하고 해당 구역을 확인해 주세요.",
    "ERROR":         "⚠️ 시스템 장애 관련 문의입니다. 카메라 연결 상태를 점검해 주세요.",
    "GENERAL":       "💬 일반 대화로 분류되었습니다. 보안 질문을 입력해 주세요.",
}

@app.post("/api/search")
async def process_user_query(request: SearchRequest):
    query_text = request.query
    session_id = request.session_id

    # 1. 대화 메모리 로드
    memory = SESSION_MEMORY.get(session_id, {})
    
    # 지칭어(그, 거기, 그때 등) 탐지
    pronouns = ["그", "거기", "그때", "이전", "다시", "아까", "마지막", "방금", "방금 전"]
    has_pronoun = any(p in query_text for p in pronouns)

    # 2. 의도 분류 (KoELECTRA - 5종)
    intent_result = intent_service.classify(query_text)
    current_intent = intent_result.intent

    # 2-1. 일상 질의(CHITCHAT) 예외 처리 (Out-of-Distribution Handling)
    if current_intent == "CHITCHAT":
        answer = nlp_service.generate_ood_response(query_text)
        return {
            "status": "success",
            "message": "지능형 보안 AI 가이드",
            "intent_info": {
                "intent": "CHITCHAT",
                "confidence": intent_result.confidence,
                "method": intent_result.method
            },
            "answer": answer,
            "results": [],
            "ai_report": None
        }

    # 지칭어가 있는데 의도가 불분명한 경우 이전 의도 계승
    if has_pronoun and current_intent == "GENERAL" and "last_intent" in memory:
        current_intent = memory["last_intent"]
        intent_result.intent = current_intent
        context_used = True
    else:
        context_used = False

    # 3. 시간 표현 파싱 (새로운 파서 사용)
    parsed_time = time_parser.parse(query_text)
    
    if not parsed_time and has_pronoun and "last_time" in memory:
        time_info = memory["last_time"]
        context_used = True
    elif parsed_time:
        time_info = {
            "start_time": parsed_time.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": parsed_time.end.strftime("%Y-%m-%d %H:%M:%S"),
            "raw": parsed_time.raw_expression
        }
    else:
        time_info = {"start_time": None, "end_time": None, "raw": "전체"}

    # 5. 의도별 라우팅 및 검색
    response_data = {
        "status": "success",
        "message": INTENT_MESSAGES.get(current_intent, "요청을 처리했습니다."),
        "intent_info": {
            "intent": current_intent,
            "confidence": intent_result.confidence,
            "method": intent_result.method
        },
        "time_info": time_info,
        "context_used": context_used,
        "results": [],
        "ai_report": None
    }

    # 검색이 필요한 의도인 경우 (대부분의 보안 질의)
    if current_intent in ("SUMMARIZATION", "BEHAVIORAL", "CAUSAL", "COUNTING", "LOCALIZATION"):
        # [Cloud Native] Supabase Vector DB에서 검색 수행
        search_results = vector_db_service.search(query=query_text, top_k=request.top_k)
        response_data["results"] = search_results
        
        # [Advanced RAG] 검색 결과를 바탕으로 AI 보안 보고서 생성
        if search_results:
            ai_report = nlp_service.generate_security_report(query=query_text, contexts=search_results)
            response_data["ai_report"] = ai_report

    # 세션 메모리 업데이트
    SESSION_MEMORY[session_id] = {
        "last_intent": current_intent,
        "last_time": time_info,
        "last_query": query_text
    }

    # 최종 로그 기록 (AI 보고서 포함)
    db_service.log_search(
        query=query_text, 
        intent=current_intent, 
        ai_report=response_data.get("ai_report") or response_data.get("answer")
    )

    return response_data

# 🚨 [신규] 실시간 이상 행동 시뮬레이션 엔드포인트
@app.post("/api/alerts/simulate")
async def simulate_realtime_event(description: str, image_path: Optional[str] = None):
    """
    CCTV 시스템에서 새로운 이벤트가 감지된 상황을 시뮬레이션합니다.
    """
    alert = alert_service.process_new_event(description, image_path)
    if alert:
        return {
            "status": "alert",
            "message": "[위험] 상황이 감지되었습니다!",
            "data": alert
        }
    return {
        "status": "normal",
        "message": "감지된 이상 행동이 없습니다."
    }

# 🚨 [신규] 최신 알림 목록 조회
@app.get("/api/alerts/latest")
async def get_latest_alerts():
    return alert_service.get_latest_alerts()

# 📸 [신규] 이미지 기반 유사 인물 검색 API
@app.post("/api/search/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = 3):
    """
    사용자가 업로드한 이미지를 기반으로 유사한 CCTV 장면을 검색합니다.
    """
    # 임시 파일 저장 경로
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # 파일 저장
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 이미지 검색 수행
        results = image_search_service.search(temp_file_path, top_k=top_k)
        
        return {
            "status": "success",
            "message": f"이미지 기반 유사도 검색 결과 {len(results)}건을 발견했습니다.",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": f"이미지 검색 중 오류 발생: {str(e)}"}
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
