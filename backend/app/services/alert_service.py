from app.services.intent_classifier import intent_service
from app.services.database import db_service
from datetime import datetime

class AlertService:
    def __init__(self):
        self.alert_history = []
        print("[Service] 실시간 이상 행동 알림 서비스 초기화 완료!")

    def process_new_event(self, description: str, image_path: str = None):
        """
        새로운 CCTV 이벤트(장면 묘사)가 들어왔을 때 위험 여부 및 범죄 유형을 판단합니다.
        """
        result = intent_service.classify(description)
        
        if result.intent == "BEHAVIORAL" and result.confidence > 0.5:
            # 범죄 세부 유형 판별 (무인 편의점 특화)
            alert_type = "CRITICAL_ALERT"
            title = "[위험] 이상 행동 실시간 감지"
            
            if any(kw in description for kw in ["불", "연기", "라이터", "방화"]):
                alert_type = "FIRE_ALERT"
                title = "[긴급] 방화 및 화재 징후 감지"
            elif any(kw in description for kw in ["싸움", "폭행", "때림", "밀침"]):
                alert_type = "VIOLENCE_ALERT"
                title = "[긴급] 폭행 및 난동 상황 감지"
            elif any(kw in description for kw in ["훔침", "절도", "몰래", "넣음", "가방"]):
                alert_type = "THEFT_ALERT"
                title = "[경고] 절도 및 무단 반출 의심"

            alert_data = {
                "id": len(self.alert_history) + 1,
                "type": alert_type,
                "title": title,
                "message": f"현장 상황: {description}",
                "location": "무인 편의점 내부",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_path": image_path,
                "confidence": round(result.confidence, 2)
            }
            self.alert_history.append(alert_data)
            
            # Supabase에 실시간 알림 저장
            db_service.save_alert({
                "type": alert_type,
                "severity": alert_type,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "image_path": image_path
            })
            
            print(f"\n[ALERT TRIGGERED - {alert_type}] {alert_data['title']}")
            print(f"상세내용: {alert_data['message']}\n")
            return alert_data
        
        return None

    def get_latest_alerts(self, count: int = 5):
        return self.alert_history[-count:]

# 싱글톤 인스턴스 생성
alert_service = AlertService()
