import os
import json
import random
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 로드
load_dotenv()

def seed_cctv_videos():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    # 1. JSON 데이터 로드
    json_path = os.path.join('ai', 'data', 'scene_descriptions.json')
    if not os.path.exists(json_path):
        print(f"[Error] {json_path} 파일이 없습니다.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        scenes = json.load(f)

    print(f"[Seed] 총 {len(scenes)}개의 장면 데이터를 업로드합니다...")

    # 2. 데이터 변환 및 업로드
    # id 필드를 제외하여 Supabase가 자동으로 UUID를 생성하도록 함
    batch_data = []
    for i, scene in enumerate(scenes):
        event_date = (datetime.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))).isoformat()
        video_filename = f"cctv_record_{i+1:03d}.mp4"
        
        data = {
            "video_filename": video_filename,
            "event_date": event_date,
            "summary": scene.get("description", "설명 없음")
        }
        batch_data.append(data)
        
        if len(batch_data) >= 20:
            try:
                supabase.table('cctv_videos').insert(batch_data).execute()
                print(f"--- {i+1}번째까지 업로드 완료...")
                batch_data = []
            except Exception as e:
                print(f"[Error] 업로드 실패: {e}")
                batch_data = []


    # 남은 데이터 업로드
    if batch_data:
        supabase.table('cctv_videos').upsert(batch_data).execute()

    print("\n✨ 데이터 업로드가 완료되었습니다! 이제 백엔드 서버를 재시작하거나 /api/search를 호출하면 새로운 데이터를 검색합니다.")

if __name__ == "__main__":
    seed_cctv_videos()
