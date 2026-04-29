import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class SupabaseService:
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        if not url or not key:
            print("[Warning] Supabase 설정이 없습니다. 로그 저장 기능이 비활성화됩니다.")
            self.supabase = None
            return
        self.supabase: Client = create_client(url, key)
        print("[Service] Supabase 클라우드 DB 연동 완료!")

    def log_search(self, query: str, intent: str, ai_report: str = None):
        if not self.supabase:
            print(f"[Mock DB] 로그 기록 (DB 연결 없음): {query} / {intent}")
            return
        try:
            # Supabase 'search_logs' 테이블에 데이터 전송
            data = {
                "query": query,
                "intent": intent
            }
            if ai_report:
                data["ai_report"] = ai_report
                
            response = self.supabase.table('search_logs').insert(data).execute()
        except Exception as e:
            print(f"[Supabase Error] 로그 저장 실패: {e}")

    def save_alert(self, alert_data: dict):
        """
        실시간 감지된 이상 행동 알림을 Supabase 'alerts' 테이블에 저장합니다.
        """
        if not self.supabase:
            print(f"[Mock DB] 알림 기록 (DB 연결 없음): {alert_data.get('type')}")
            return
        try:
            response = self.supabase.table('alerts').insert(alert_data).execute()
            print(f"[Supabase] 실시간 알림 DB 저장 성공: {alert_data.get('type')}")
        except Exception as e:
            # 테이블이 없거나 권한 문제일 수 있으므로 에러 메시지 출력
            print(f"[Supabase Error] 알림 저장 실패: {e}")

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
db_service = SupabaseService()
