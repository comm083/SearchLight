import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.schemas import SearchRequest, SearchResponse, HistoryResponse, AlertSimulationRequest
from app.services.search_manager import search_manager
from app.services.database import db_service
from app.services.nlp_service import nlp_service
from app.services.alert_service import alert_service
from app.services.image_search_service import image_search_service

app = FastAPI(title="SearchLight CCTV 통합 검색 API", version="3.0")

# 정적 파일 서빙
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/search", response_model=SearchResponse)
async def process_user_query(request: SearchRequest):
    """지능형 보안 검색 및 분석 수행"""
    return search_manager.handle_query(
        query_text=request.query,
        session_id=request.session_id,
        top_k=request.top_k
    )

@app.get("/api/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """사용자의 이전 검색 기록 조회"""
    return {
        "status": "success",
        "history": db_service.get_search_history(session_id)
    }

@app.delete("/api/history/{history_id}")
async def delete_history(history_id: str):
    """특정 검색 기록 삭제"""
    success = db_service.delete_search_history(history_id)
    if success:
        return {"status": "success", "message": "기록이 삭제되었습니다."}
    return {"status": "error", "message": "삭제 실패"}

@app.post("/api/alerts/simulate")
async def simulate_realtime_event(request: AlertSimulationRequest):
    """이상 행동 시뮬레이션"""
    alert = alert_service.process_new_event(request.description, request.image_path)
    if alert:
        return {"status": "alert", "message": "[위험] 상황 감지!", "data": alert}
    return {"status": "normal", "message": "정상 상황"}

@app.get("/api/alerts/latest")
async def get_latest_alerts():
    """최신 알림 목록 조회"""
    return alert_service.get_latest_alerts()

@app.post("/api/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """OpenAI Whisper를 사용한 음성 인식"""
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, f"stt_{file.filename}")
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text = nlp_service.transcribe_audio(temp_file_path)
        return {"status": "success", "text": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/search/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = 3):
    """이미지 기반 유사 장면 검색"""
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        results = image_search_service.search(temp_file_path, top_k=top_k)
        return {
            "status": "success",
            "message": f"검색 결과 {len(results)}건 발견",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
