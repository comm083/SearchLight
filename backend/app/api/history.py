from fastapi import APIRouter
from app.services.database import db_service

router = APIRouter()

@router.get("/{session_id}")
async def get_history(session_id: str):
    """
    사용자의 이전 검색 기록을 가져옵니다.
    """
    history = db_service.get_search_history(session_id)
    return {
        "status": "success",
        "history": history
    }
