from datetime import datetime
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

        print("[Service] event/event_intents 기반 FAISS 검색 서비스 초기화 중...")
        self.model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        self.scene_data: List[Dict] = []
        self.index = None

        self._build_index()
        print("[Service] FAISS 인덱스 구축 완료!")

    def _build_index(self):
        try:
            resp = self.supabase.table('event').select('*, event_intents(*), event_clips(*)').execute()
            rows = resp.data or []

            self.scene_data = []
            for row in rows:
                intents_list = row.get('event_intents') or []
                intents = intents_list[0] if intents_list else {}

                search_text = ' '.join(filter(None, [
                    row.get('summary', ''),
                    intents.get('time_sent', ''),
                    intents.get('count_sent', ''),
                    intents.get('action_sent', ''),
                    intents.get('info_sent', ''),
                    intents.get('error_sent', ''),
                ]))

                event_clips_list = row.get('event_clips') or []
                first_clip_url = event_clips_list[0].get('clip_url') if event_clips_list else row.get('clip_url')

                self.scene_data.append({
                    "id":             row['id'],
                    "summary":        row.get('summary', ''),
                    "description":    row.get('summary', ''),
                    "search_text":    search_text,
                    "event_date":     row.get('timestamp'),
                    "video_filename": row.get('video_filename'),
                    "clip_url":       first_clip_url,
                    "situation":      row.get('situation'),
                    "count_people":   row.get('count_people', 0),
                })

        except Exception as e:
            print(f"[Vector DB Error] 데이터 로드 실패: {e}")
            self.scene_data = []

        if not self.scene_data:
            print("[Vector DB 경고] 데이터 없음 - 검색 비활성화")
            return

        search_texts = [item.get("search_text", "") for item in self.scene_data]
        embeddings = self.model.encode(search_texts).astype('float32')
        faiss.normalize_L2(embeddings)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        print(f"[Vector DB] event 테이블 기반 {len(self.scene_data)}개 이벤트로 FAISS 인덱스 구축 완료.")

    def search(self, query: str, top_k: int = 3, start_time: str = None, end_time: str = None, threshold: float = 0.35) -> List[Dict]:
        if self.index is None or not self.scene_data:
            return []

        def parse_dt(dt_str):
            if not dt_str: return None
            try:
                if 'T' in str(dt_str):
                    dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
                    if dt.tzinfo is not None:
                        from datetime import timezone, timedelta as td
                        kst = timezone(td(hours=9))
                        dt = dt.astimezone(kst).replace(tzinfo=None)
                    return dt
                return datetime.strptime(str(dt_str), "%Y-%m-%d %H:%M:%S")
            except:
                return None

        filtered_data = self.scene_data
        if start_time or end_time:
            temp_filtered = []
            st = parse_dt(start_time)
            et = parse_dt(end_time)
            for item in self.scene_data:
                item_time = parse_dt(item.get("event_date"))
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

        search_k = len(self.scene_data)
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

        if not candidates and filtered_data and (start_time or end_time):
            sorted_filtered = sorted(
                filtered_data,
                key=lambda x: x.get("event_date") or "",
                reverse=True
            )
            candidates = [(item, 0.0) for item in sorted_filtered[:top_k]]

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
                "frames":         [],
                "score":          round(float(score), 4),
                "clip_url":       item.get("clip_url"),
                "situation":      item.get("situation"),
                "count_people":   item.get("count_people", 0),
            })

        print(f"[Vector DB] {len(results)}개 유사 이벤트 검색 완료.")
        return results

    def reload(self):
        self._build_index()


# 싱글톤 인스턴스
vector_db_service = VectorDBService()
