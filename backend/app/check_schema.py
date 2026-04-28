import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def check_supabase_schema():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("[Error] .env 파일에 SUPABASE_URL 또는 SUPABASE_KEY가 없습니다.")
        return

    supabase: Client = create_client(url, key)
    
    print(f"\n[Supabase 스키마 체크] 연결 대상: {url}")
    
    # 1. search_logs 테이블 확인 (데이터 한 건을 가져와서 컬럼 구조 파악)
    print("\n1. 'search_logs' 테이블 구조 확인 중...")
    try:
        res = supabase.table('search_logs').select("*").limit(1).execute()
        if res.data:
            columns = res.data[0].keys()
            print(f"[SUCCESS] 'search_logs' 테이블 존재함. 현재 컬럼: {list(columns)}")
            
            # 필수 컬럼 체크
            required = ['query', 'intent', 'ai_report', 'session_id']
            missing = [c for c in required if c not in columns]
            if missing:
                print(f"[WARNING] 누락된 권장 컬럼: {missing}")
            else:
                print("[INFO] 모든 권장 컬럼이 정상적으로 존재합니다!")
        else:
            print("[INFO] 'search_logs' 테이블은 존재하나 데이터가 없어 구조를 확정할 수 없습니다.")
    except Exception as e:
        print(f"[ERROR] 'search_logs' 테이블 확인 실패: {e}")

    # 2. alerts 테이블 확인
    print("\n2. 'alerts' 테이블 구조 확인 중...")
    try:
        res = supabase.table('alerts').select("*").limit(1).execute()
        if res.data:
            columns = res.data[0].keys()
            print(f"[SUCCESS] 'alerts' 테이블 존재함. 현재 컬럼: {list(columns)}")
            
            required = ['type', 'severity', 'description', 'image_path', 'confidence']
            missing = [c for c in required if c not in columns]
            if missing:
                print(f"[WARNING] 누락된 권장 컬럼: {missing}")
            else:
                print("[INFO] 모든 권장 컬럼이 정상적으로 존재합니다!")
        else:
            print("[INFO] 'alerts' 테이블은 존재하나 데이터가 없어 구조를 확정할 수 없습니다.")
    except Exception as e:
        print(f"[ERROR] 'alerts' 테이블 확인 실패: {e}")

if __name__ == "__main__":
    check_supabase_schema()
