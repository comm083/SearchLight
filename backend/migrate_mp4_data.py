import json
import os
import sys
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def migrate_mp4_data():
    # 1. Supabase 연결 설정
    url = os.getenv("SUPABASE_URL")
    # 서비스 키 우선 사용 (RLS 우회)
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return
    supabase: Client = create_client(url, key)

    # 2. SBERT 모델 로드
    print("[Step 1] SBERT 모델 로드 중 (jhgan/ko-sroberta-multitask)...")
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')

    # 3. mp4_JsonData.json 로드
    json_path = os.path.join('..', 'ai', 'data', 'mp4_JsonData.json')
    if not os.path.exists(json_path):
        # 상대 경로 재시도 (실행 위치에 따라 다를 수 있음)
        json_path = os.path.join('ai', 'data', 'mp4_JsonData.json')
        
    print(f"[Step 2] {json_path} 데이터 읽는 중...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # 4. 데이터 업로드
    print(f"[Step 3] 총 {len(data)}개의 영상 데이터를 Supabase에 업로드합니다...")

    for idx, item in enumerate(data):
        summary = item.get('summary', '')
        video_filename = item.get('video_filename', '')
        event_date = item.get('event_date', None)
        frames = item.get('frames', [])

        # 4-1. cctv_videos 테이블에 메타데이터 저장
        try:
            # 중복 체크
            existing = supabase.table('cctv_videos').select('id').eq('video_filename', video_filename).execute()
            if existing.data:
                video_id = existing.data[0]['id']
                supabase.table('cctv_videos').update({
                    "summary": summary,
                    "frames": frames
                }).eq('id', video_id).execute()
                print(f"  [{idx+1}/{len(data)}] {video_filename} 업데이트 완료")
            else:
                result = supabase.table('cctv_videos').insert({
                    "video_filename": video_filename,
                    "event_date": event_date,
                    "summary": summary,
                    "frames": frames
                }).execute()
                video_id = result.data[0]['id']
                print(f"  [{idx+1}/{len(data)}] {video_filename} 저장 완료")

            # 4-2. cctv_vectors 테이블에 검색용 벡터 저장 (업데이트 또는 삽입)
            # SBERT 임베딩 생성
            embedding = model.encode(summary).tolist()
            
            metadata = {
                "timestamp": event_date or "2026-04-28 00:00:00",
                "image_path": f"/static/images/video_thumb.png", # 썸네일 경로 (가상)
                "location": "무인 편의점 내부",
                "video_id": str(video_id),
                "video_filename": video_filename
            }

            existing_vector = supabase.table('cctv_vectors').select('id').eq('metadata->>video_filename', video_filename).execute()
            
            if existing_vector.data:
                supabase.table('cctv_vectors').update({
                    "content": summary,
                    "metadata": metadata,
                    "embedding": embedding
                }).eq('id', existing_vector.data[0]['id']).execute()
            else:
                supabase.table('cctv_vectors').insert({
                    "content": summary,
                    "metadata": metadata,
                    "embedding": embedding
                }).execute()
            print(f"    -> 검색 벡터 등록/업데이트 완료")

        except Exception as e:
            print(f"  [{idx+1}/{len(data)}] ERROR: {e}")

    print("\n✨ 모든 실제 데이터가 Supabase 클라우드(cctv_videos, cctv_vectors)에 통합 업로드되었습니다!")

if __name__ == "__main__":
    migrate_mp4_data()
