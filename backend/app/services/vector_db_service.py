import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class VectorDBService:
    def __init__(self):
        # Supabase 연결
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)
        
        # SBERT 모델 로드 (질의 벡터화용)
        print("[Service] Supabase Vector Search 서비스 초기화 중...")
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        print("[Service] 벡터 검색 모델 로드 완료!")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        사용자의 질문을 벡터로 변환하여 Supabase에서 유사한 장면을 검색합니다.
        """
        # 1. 질의 벡터화
        query_embedding = self.model.encode(query).tolist()

        # 2. Supabase RPC(함수) 호출 또는 직접 검색
        # 참고: Supabase에서 벡터 검색을 수행하려면 rpc 호출이 가장 효율적입니다.
        try:
            # 매치 함수 호출 (미리 정의된 match_cctv_vectors SQL 함수 사용)
            response = self.supabase.rpc('match_cctv_vectors', {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': top_k
            }).execute()

            results = []
            for item in response.data:
                results.append({
                    "description": item['content'],
                    "timestamp": item['metadata'].get('timestamp'),
                    "image_path": item['metadata'].get('image_path'),
                    "location": item['metadata'].get('location'),
                    "score": item['similarity']
                })
            
            print(f"[Vector DB] {len(results)}개의 유사 장면을 클라우드에서 찾았습니다.")
            return results

        except Exception as e:
            print(f"[Vector DB Error] 검색 실패: {e}")
            return []

# 싱글톤 인스턴스
vector_db_service = VectorDBService()
