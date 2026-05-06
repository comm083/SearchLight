from fastapi import APIRouter
from app.schemas import HistoryResponse
from app.services.database import db_service

router = APIRouter()

@router.get("/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """사용자의 이전 검색 기록 조회"""
    return {
        "status": "success",
        "history": db_service.get_search_history(session_id)
    }

@router.delete("/{history_id}")
async def delete_history(history_id: str):
    """특정 검색 기록 삭제"""
    success = db_service.delete_search_history(history_id)
    if success:
        return {"status": "success", "message": "기록이 삭제되었습니다."}
    return {"status": "error", "message": "삭제 실패"}

from pydantic import BaseModel

class FeedbackRequest(BaseModel):
    history_id: int = None
    session_id: str = None
    feedback_type: str
    comment: str = None

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """검색 결과 피드백 제출 (FP/FN 수집)"""
    # session_id가 제공된 경우 가장 최근 로그의 id를 찾아서 업데이트
    target_id = request.history_id
    if not target_id and request.session_id:
        logs = db_service.get_search_history(request.session_id, limit=1)
        if logs and len(logs) > 0:
            target_id = logs[0]['id']
            
    if not target_id:
        return {"status": "error", "message": "피드백을 기록할 대상을 찾을 수 없습니다."}
        
    success = db_service.log_feedback(target_id, request.feedback_type, request.comment)
    if success:
        return {"status": "success", "message": "피드백이 접수되었습니다."}
    return {"status": "error", "message": "피드백 접수 실패"}
