import os
import faiss
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

OLDEST_KEYWORDS = ["오래된", "옛날", "예전", "처음", "가장 오래", "오래전", "이전"]
NEWEST_KEYWORDS = ["최근", "방금", "아까", "요즘", "새로운", "가장 최근", "최신"]


class VectorDBService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

        print("[Service] Supabase cctv_videos 기반 FAISS 검색 서비스 초기화 중...")
        self.model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        self.scene_data: List[Dict] = []
        self.index = None

        self._build_index()
        print("[Service] FAISS 인덱스 구축 완료!")

    def _build_index(self):
        try:
            # frames 컬럼이 없을 수 있으므로 예외 처리 강화
            response = self.supabase.table('cctv_videos').select(
                'id, video_filename, event_date, summary'
            ).execute()
            self.scene_data = response.data or []
        except Exception as e:
            print(f"[Vector DB Error] cctv_videos 로드 실패: {e}")
            self.scene_data = []

        if not self.scene_data:
            print("[Vector DB 경고] cctv_videos 데이터 없음 - 검색 비활성화")
            return

        summaries = [item.get("summary", "") for item in self.scene_data]
        embeddings = self.model.encode(summaries).astype('float32')
        faiss.normalize_L2(embeddings)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        print(f"[Vector DB] {len(self.scene_data)}개 영상 데이터로 인덱스 구축 완료.")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if self.index is None or not self.scene_data:
            return []

        is_oldest = any(kw in query for kw in OLDEST_KEYWORDS)
        is_newest = any(kw in query for kw in NEWEST_KEYWORDS)
        k = min(len(self.scene_data), max(top_k, 3) if (is_oldest or is_newest) else top_k)

        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)
        scores, indices = self.index.search(query_embedding, k)

        candidates = [self.scene_data[idx] for idx in indices[0] if idx < len(self.scene_data)]

        if is_oldest or is_newest:
            candidates = sorted(
                candidates,
                key=lambda x: x.get("event_date") or "",
                reverse=is_newest
            )

        results = []
        for i, item in enumerate(candidates[:top_k]):
            results.append({
                "rank":           i + 1,
                "description":    item.get("summary", ""),
                "video_filename": item.get("video_filename"),
                "event_date":     item.get("event_date"),
                "frames":         item.get("frames", []),
                "distance":       round(1 - float(scores[0][i]), 4) if i < len(scores[0]) else 1.0,
                "image_path":     None,
                "video_url":      f"/static/mp4Data/{item.get('video_filename', '')}",
            })

        print(f"[Vector DB] {len(results)}개 유사 장면 검색 완료.")
        return results

    def reload(self):
        """영상 추가 후 인덱스를 다시 빌드합니다."""
        self._build_index()


# 싱글톤 인스턴스
vector_db_service = VectorDBService()
