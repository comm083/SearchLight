import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class SupabaseService:
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)
        print("[Service] Supabase 클라우드 DB 연동 완료!")

    def log_search(self, query: str, intent: str):
        try:
            # Supabase 'search_logs' 테이블에 데이터 전송
            response = self.supabase.table('search_logs').insert({
                "query": query,
                "intent": intent
            }).execute()
        except Exception as e:
            print(f"[Supabase Error] 로그 저장 실패: {e}")

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
db_service = SupabaseService()
