import datetime
from supabase import create_client, Client

class SupabaseService:
    def __init__(self):
        url: str = "https://nnuetzqcbnnkarzuqaeh.supabase.co"
        # 팀장님이 전달해주신 JWT anon public 키
        key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5udWV0enFjYm5ua2FyenVxYWVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwMDczODAsImV4cCI6MjA5MjU4MzM4MH0.kp6qof8vnlORn6Doluydsaatwm3y4QuAqMleYtteyEo"
        self.supabase: Client = create_client(url, key)
        print("[Service] Supabase 클라우드 DB 연동 완료!")

    def log_search(self, query: str, intent: str):
        try:
            current_time = datetime.datetime.now().isoformat()
            # Supabase 'search_logs' 테이블에 데이터 전송
            # created_at (timestamp)는 Supabase가 자동 생성함을 가정합니다. 
            # 단, 이전에 SQLite에서 썼던 'timestamp' 컬럼명이 테이블에 존재한다면 에러가 날 수 있으니
            # 테이블 설정 시 timestamp 컬럼을 만들거나 제외하세요.
            response = self.supabase.table('search_logs').insert({
                "query": query,
                "intent": intent
            }).execute()
        except Exception as e:
            print(f"[Supabase Error] 로그 저장 실패: {e}")

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
db_service = SupabaseService()
