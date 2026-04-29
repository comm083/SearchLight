from fastapi import APIRouter
from typing import Optional
from app.services.alert_service import alert_service

router = APIRouter()

@router.post("/simulate")
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

@router.get("/latest")
async def get_latest_alerts():
    """최신 알림 목록을 반환합니다."""
    return alert_service.get_latest_alerts()
