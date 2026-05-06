from fastapi import APIRouter
from app.schemas import AlertSimulationRequest
from app.services.alert_service import alert_service

router = APIRouter()

@router.post("/simulate")
async def simulate_realtime_event(request: AlertSimulationRequest):
    """이상 행동 시뮬레이션"""
    alert = alert_service.process_new_event(request.description, request.image_path)
    if alert:
        return {"status": "alert", "message": "[위험] 상황 감지!", "data": alert}
    return {"status": "normal", "message": "정상 상황"}

@router.get("/latest")
async def get_latest_alerts():
    """최신 알림 목록 조회"""
    return alert_service.get_latest_alerts()
