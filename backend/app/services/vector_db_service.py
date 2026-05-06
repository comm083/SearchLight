from datetime import datetime
import os
import faiss
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from app.core.config import settings
from app.core.constants import KEYWORDS


class VectorDBService:
    def __init__(self):
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
        self.supabase: Client = create_client(url, key)

        print("[Service] Supabase cctv_videos 기반 FAISS 검색 서비스 초기화 중...")
        self.model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        self.scene_data: List[Dict] = []
        self.index = None

        self._build_index()
        print("[Service] FAISS 인덱스 구축 완료!")

    def _build_index(self):
        try:
            # 1. 실제 비디오 상세 데이터 로드 (frames 컬럼이 없을 수 있으므로 유연하게 처리)
            video_resp = self.supabase.table('cctv_videos').select('*').execute()
            video_map = {str(v['id']): v for v in (video_resp.data or [])}
            
            # 2. 검색 벡터 데이터 로드
            vector_resp = self.supabase.table('cctv_vectors').select('id, content, metadata').execute()
            vector_data = vector_resp.data or []
            
            self.scene_data = []
            for v in vector_data:
                meta = v.get('metadata', {})
                video_id = meta.get('video_id')
                
                video_info = video_map.get(video_id) if video_id else None
                
                item = {
                    "id":             v['id'],
                    "summary":        v['content'],
                    "description":    v['content'],
                    "image_path":     meta.get('image_path') or "/static/images/default_thumb.png",
                    "location":       meta.get('location', '보안 구역'),
                    "event_date":     meta.get('timestamp'),
                    "video_filename": meta.get('video_filename') or (video_info.get('video_filename') if video_info else None),
                    "frames":         video_info.get('frames', []) if video_info else []
                }
                self.scene_data.append(item)
                
        except Exception as e:
            print(f"[Vector DB Error] 데이터 로드 및 인덱스 구축 실패: {e}")
            self.scene_data = []

        if not self.scene_data:
            print("[Vector DB 경고] 데이터 없음 - 검색 비활성화")
            return

        summaries = [item.get("summary", "") for item in self.scene_data]
        embeddings = self.model.encode(summaries).astype('float32')
        faiss.normalize_L2(embeddings)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        print(f"[Vector DB] 총 {len(self.scene_data)}개 장면 데이터로 인덱스 통합 구축 완료.")

    def search(self, query: str, top_k: int = 3, start_time: str = None, end_time: str = None, threshold: float = 0.45) -> List[Dict]:
        if self.index is None or not self.scene_data:
            return []

        def parse_dt(dt_str):
            if not dt_str: return None
            try:
                if 'T' in dt_str:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except:
                return None

        # 1. 시간 필터링 적용
        filtered_data = self.scene_data
        if start_time or end_time:
            temp_filtered = []
            st = parse_dt(start_time)
            et = parse_dt(end_time)

            for item in self.scene_data:
                item_time_str = item.get("event_date")
                item_time = parse_dt(item_time_str)
                
                if not item_time:
                    temp_filtered.append(item)
                    continue
                
                if st and item_time < st: continue
                if et and item_time > et: continue
                
                temp_filtered.append(item)
            filtered_data = temp_filtered

        if not filtered_data:
            return []

        is_oldest = any(kw in query for kw in KEYWORDS["OLDEST"])
        is_newest = any(kw in query for kw in KEYWORDS["NEWEST"])
        
        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        search_k = min(len(self.scene_data), 50) 
        scores, indices = self.index.search(query_embedding, search_k)

        candidates = []
        filtered_ids = {id(item) for item in filtered_data}
        
        for i, idx in enumerate(indices[0]):
            if idx < len(self.scene_data):
                item = self.scene_data[idx]
                score = scores[0][i]
                if id(item) in filtered_ids and score >= threshold:
                    candidates.append((item, score))
            
            if len(candidates) >= top_k:
                break

        if is_oldest or is_newest:
            candidates.sort(
                key=lambda x: x[0].get("event_date") or "",
                reverse=is_newest
            )

        results = []
        for i, (item, score) in enumerate(candidates[:top_k]):
            results.append({
                "rank":           i + 1,
                "description":    item.get("summary", ""),
                "video_filename": item.get("video_filename"),
                "event_date":     item.get("event_date"),
                "timestamp":      item.get("event_date"), 
                "frames":         item.get("frames", []),
                "score":          round(float(score), 4),
                "image_path":     item.get("image_path") or "/static/images/default_thumb.png",
                "video_url":      f"/static/mp4Data/{item.get('video_filename', '')}",
            })

        print(f"[Vector DB] {len(results)}개 유사 장면 검색 완료 (필터링 적용).")

        return results

    def reload(self):
        """영상 추가 후 인덱스를 다시 빌드합니다."""
        self._build_index()


# 싱글톤 인스턴스
vector_db_service = VectorDBService()
