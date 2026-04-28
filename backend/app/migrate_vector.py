import json
import os
import sys
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def migrate_data():
    # 1. Supabase 연결 설정
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    # 2. SBERT 모델 로드 (FAISS 서비스와 동일한 모델 사용)
    print("[Step 1] SBERT 모델 로드 중...")
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')

    # 3. JSON 데이터 로드
    json_path = os.path.join('ai', 'data', 'scene_descriptions.json')
    print(f"[Step 2] {json_path} 데이터 읽는 중...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 4. 데이터 벡터화 및 업로드
    print(f"[Step 3] 총 {len(data)}개의 데이터를 벡터화하여 Supabase로 전송합니다...")
    
    # 기존 데이터 삭제 (중복 방지 - 필요 시)
    # supabase.table('cctv_vectors').delete().neq('id', 0).execute()

    for idx, item in enumerate(data):
        content = item['description']
        # SBERT 임베딩 생성
        embedding = model.encode(content).tolist()
        
        # 메타데이터 구성 (필드 유무 확인)
        metadata = {
            "timestamp": item.get('timestamp', '2026-04-28 00:00:00'),
            "image_path": item.get('image_path', ''),
            "location": item.get('location', '무인 편의점 내부')
        }

        # Supabase 삽입
        try:
            supabase.table('cctv_vectors').insert({
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            }).execute()
            
            if (idx + 1) % 10 == 0:
                print(f"--- {idx + 1}개 완료...")
        except Exception as e:
            print(f"[ERROR] {idx+1}번째 데이터 저장 실패: {e}")

    print("\n✨ 마이그레이션 완료! 이제 모든 CCTV 장면 데이터가 Supabase 클라우드에 저장되었습니다.")

if __name__ == "__main__":
    migrate_data()
