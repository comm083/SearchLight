import faiss
import json
import os
from sentence_transformers import SentenceTransformer

class FaissSearchService:
    def __init__(self):
        print("[Service] FAISS 검색 엔진 초기화 중...")
        self.model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        
        # JSON 데이터 로드
        json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ai', 'data', 'scene_descriptions.json'))
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.db_descriptions = [item["description"] for item in data]
                print(f"[Service] -> {len(self.db_descriptions)}건의 장면 묘사 데이터를 로드했습니다.")
        except FileNotFoundError:
            print(f"[Service] 오류: {json_path} 파일을 찾을 수 없습니다.")
            self.db_descriptions = ["데이터 로드 실패 - 기본 더미 텍스트"]
        
        # 인덱싱 준비
        db_embeddings = self.model.encode(self.db_descriptions).astype('float32')
        self.dimension = db_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(db_embeddings)
        print("[Service] FAISS 검색 엔진 로드 완료!")

    def search(self, query: str, top_k: int = 2):
        query_embedding = self.model.encode([query]).astype('float32')
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i in range(top_k):
            idx = indices[0][i]
            dist = float(distances[0][i])
            results.append({
                "rank": i + 1,
                "description": self.db_descriptions[idx],
                "distance": round(dist, 4)
            })
        return results

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
faiss_service = FaissSearchService()
