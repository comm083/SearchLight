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
    comment: str = None  # JSON 문자열: {"comment": "...", "correct_event_id": "uuid"}

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """검색 결과 피드백 제출 (코멘트 + 정답 영상 ID)"""
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

@router.get("/feedbacks")
async def get_feedbacks(status: str = "pending"):
    """관리자용 피드백 목록 조회 (status: pending | resolved | all)"""
    return db_service.get_feedbacks(status)

@router.post("/feedback/{feedback_id}/resolve")
async def resolve_feedback(feedback_id: int):
    """피드백 처리 완료 마크"""
    success = db_service.resolve_feedback(feedback_id)
    if success:
        return {"status": "success", "message": "처리 완료로 변경되었습니다."}
    return {"status": "error", "message": "처리 실패"}

@router.post("/feedback/{feedback_id}/boost")
async def boost_event(feedback_id: int):
    """정답 이벤트의 검색 가중치 향상 + 처리 완료 마크"""
    success = db_service.boost_event_from_feedback(feedback_id)
    if success:
        return {"status": "success", "message": "품질 개선이 적용되었습니다."}
    return {"status": "error", "message": "적용 실패 (정답 영상이 선택되지 않았거나 오류 발생)"}
