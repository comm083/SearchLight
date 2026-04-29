import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

def check_data():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    try:
        # cctv_vectors 테이블에서 상위 5개 데이터 가져오기
        response = supabase.table('cctv_vectors').select("*").limit(5).execute()
        
        if response.data:
            print(f"\n[성공] 'cctv_vectors' 테이블에서 {len(response.data)}개의 데이터를 가져왔습니다.\n")
            for i, item in enumerate(response.data):
                print(f"--- 데이터 #{i+1} ---")
                print(f"ID: {item.get('id')}")
                print(f"내용(Content): {item.get('content')}")
                print(f"메타데이터: {json.dumps(item.get('metadata'), indent=2, ensure_ascii=False)}")
                print("-" * 20)
        else:
            print("\n[알림] 테이블에 데이터가 없습니다.")
            
    except Exception as e:
        print(f"\n[오류] 데이터 조회 실패: {e}")

if __name__ == "__main__":
    check_data()
