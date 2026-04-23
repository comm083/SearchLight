import faiss
from sentence_transformers import SentenceTransformer

class FaissSearchService:
    def __init__(self):
        print("[Service] FAISS 검색 엔진 초기화 중...")
        self.model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        
        # 더미 데이터베이스
        self.db_descriptions = [
            "빨간색 패딩을 입은 남자가 골목길을 급하게 뛰어감",
            "검은색 세단이 신호를 위반하고 교차로를 지나감",
            "파란색 모자를 쓴 사람이 자전거를 타고 횡단보도를 건넘",
            "두 사람이 편의점 앞에서 대화를 나누고 있음",
            "밤늦게 한 여성이 스마트폰을 보며 걸어가고 있음"
        ]
        
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
