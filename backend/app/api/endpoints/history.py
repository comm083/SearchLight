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
