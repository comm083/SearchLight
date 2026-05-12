from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class TimestampUpdate(BaseModel):
    timestamp: str

@router.get("/events")
async def get_all_events(limit: int = 300):
    """모든 비디오 이벤트 조회 (Event History 용)"""
    from app.services.database import db_service
    return db_service.get_all_events(limit)

@router.get("/events/pending")
async def get_pending_events(limit: int = 100):
    """timestamp가 NULL인 처리대기 이벤트 조회"""
    from app.services.database import db_service
    return db_service.get_pending_events(limit)

@router.patch("/events/{event_id}/timestamp")
async def update_event_timestamp(event_id: str, body: TimestampUpdate):
    """이벤트 timestamp 수동 입력"""
    from app.services.database import db_service
    ok = db_service.update_event_timestamp(event_id, body.timestamp)
    if ok:
        return {"status": "success", "message": f"이벤트 {event_id} timestamp 업데이트 완료"}
    return {"status": "error", "message": "업데이트 실패"}

@router.post("/admin/fix-timestamps")
async def fix_timestamps():
    """기존 이벤트 타임스탬프 KST 보정 (최초 1회만 실행)"""
    from app.services.database import db_service
    from app.services.vector_db_service import vector_db_service
    result = db_service.fix_timestamps_kst()
    if result.get("status") == "success":
        vector_db_service.reload()
    return result

@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """이벤트 삭제 (관리자 전용)"""
    from app.services.database import db_service
    ok = db_service.delete_event(event_id)
    if ok:
        return {"status": "success", "message": f"이벤트 {event_id} 삭제 완료"}
    return {"status": "error", "message": "삭제 실패"}
