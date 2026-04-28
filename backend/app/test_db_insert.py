import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_insert():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    print("[Test] Supabase 연결 테스트 시작...")
    
    # 1. search_logs 테스트 데이터 삽입
    try:
        data = {
            "query": "테스트 검색 질의",
            "intent": "TEST",
            "ai_report": "이것은 데이터베이스 연결 확인을 위한 테스트 보고서입니다.",
            "session_id": "test_session_123"
        }
        res = supabase.table('search_logs').insert(data).execute()
        print(f"[SUCCESS] 'search_logs' 테스트 데이터 삽입 성공: {res.data}")
    except Exception as e:
        print(f"[ERROR] 'search_logs' 삽입 실패: {e}")

    # 2. alerts 테스트 데이터 삽입
    try:
        alert_data = {
            "type": "TEST_ALERT",
            "severity": "INFO",
            "description": "시스템 연결 테스트용 알림입니다.",
            "confidence": 1.0
        }
        res = supabase.table('alerts').insert(alert_data).execute()
        print(f"[SUCCESS] 'alerts' 테스트 데이터 삽입 성공: {res.data}")
    except Exception as e:
        print(f"[ERROR] 'alerts' 삽입 실패: {e}")

if __name__ == "__main__":
    test_insert()
