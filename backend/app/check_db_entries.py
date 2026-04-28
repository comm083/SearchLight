import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def check_db_entries():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("[Error] .env 파일에 SUPABASE_URL 또는 SUPABASE_KEY가 없습니다.")
        return

    supabase: Client = create_client(url, key)
    
    print(f"\n[데이터베이스 저장 현황 체크]")
    
    # 1. 최근 검색 로그 확인
    print("\n1. 'search_logs' 최근 3건 조회 중...")
    try:
        res = supabase.table('search_logs').select("*").order('created_at', desc=True).limit(3).execute()
        if res.data:
            print(f"[SUCCESS] 최근 검색 로그 {len(res.data)}건 발견:")
            for idx, log in enumerate(res.data):
                print(f"   [{idx+1}] 시간: {log.get('created_at')}")
                print(f"       질문: {log.get('query')}")
                print(f"       의도: {log.get('intent')}")
                print(f"       AI 보고서 요약: {str(log.get('ai_report', ''))[:50]}...")
        else:
            print("[INFO] 'search_logs'에 데이터가 아직 없습니다.")
    except Exception as e:
        print(f"[ERROR] 'search_logs' 조회 실패: {e}")

    # 2. 최근 알림 확인
    print("\n2. 'alerts' 최근 3건 조회 중...")
    try:
        res = supabase.table('alerts').select("*").order('created_at', desc=True).limit(3).execute()
        if res.data:
            print(f"[SUCCESS] 최근 위험 알림 {len(res.data)}건 발견:")
            for idx, alert in enumerate(res.data):
                print(f"   [{idx+1}] 시간: {alert.get('created_at')}")
                print(f"       유형: {alert.get('type')}")
                print(f"       심각도: {alert.get('severity')}")
                print(f"       내용: {alert.get('description')}")
        else:
            print("[INFO] 'alerts'에 데이터가 아직 없습니다.")
    except Exception as e:
        print(f"[ERROR] 'alerts' 조회 실패: {e}")

if __name__ == "__main__":
    check_db_entries()
