import os
import faiss
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

OLDEST_KEYWORDS = ["오래된", "옛날", "예전", "처음", "가장 오래", "오래전", "이전"]
NEWEST_KEYWORDS = ["최근", "방금", "아까", "요즘", "새로운", "가장 최근", "최신"]

# 의도별 키워드 → cctv_intents 필드 매핑
_INTENT_KEYWORDS = {
    "error_sent":  ["망가", "고장", "오류", "에러", "작동 안", "안 나와", "끊겼", "노이즈", "흐릿", "멈춰", "재부팅", "녹화 안"],
    "count_sent":  ["몇 명", "몇명", "몇 대", "몇대", "몇 번", "몇번", "몇 회", "몇회", "총", "집계", "통계", "인원", "명수"],
    "action_sent": ["폭행", "절도", "훔치", "도둑", "침입", "담 넘", "싸움", "싸우", "때리", "쓰러", "뛰어", "도망", "낙서", "파손", "난동", "흉기"],
    "time_sent":   ["어제", "오늘", "내일", "최근", "아까", "방금", "지금", "오전", "오후", "새벽", "아침", "점심", "저녁", "밤", "시간", "언제"],
    "info_sent":   ["요약", "정리", "보고서", "브리핑", "분석", "현황", "내역", "일지", "이력", "전체"],
}


def _detect_intent_field(query: str) -> str:
    """질문 키워드로 관련 의도 필드를 감지합니다."""
    for field, keywords in _INTENT_KEYWORDS.items():
        if any(kw in query for kw in keywords):
            return field
    return "info_sent"


class VectorDBService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

        print("[Service] Supabase cctv_videos 기반 FAISS 검색 서비스 초기화 중...")
        self.model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
        self.scene_data: List[Dict] = []
        self.index = None          # summary 기반 FAISS 인덱스
        self.intent_index = None   # 의도 문장 기반 FAISS 인덱스

        self._build_index()
        print("[Service] FAISS 인덱스 구축 완료!")

    def _build_index(self):
        # cctv_videos 로드
        try:
            response = self.supabase.table('cctv_videos').select(
                'id, video_filename, event_date, summary'
            ).execute()
            self.scene_data = response.data or []
        except Exception as e:
            print(f"[Vector DB Error] cctv_videos 로드 실패: {e}")
            self.scene_data = []

        if not self.scene_data:
            print("[Vector DB 경고] cctv_videos 데이터 없음 — 검색 비활성화")
            return

        # cctv_intents 로드 및 scene_data에 병합
        try:
            intent_response = self.supabase.table('cctv_intents').select('*').execute()
            intent_map = {row['video_id']: row for row in (intent_response.data or [])}
            for scene in self.scene_data:
                intents = intent_map.get(scene['id'], {})
                scene['intents'] = {
                    'time_sent':   intents.get('time_sent', ''),
                    'count_sent':  intents.get('count_sent', ''),
                    'action_sent': intents.get('action_sent', ''),
                    'info_sent':   intents.get('info_sent', ''),
                    'error_sent':  intents.get('error_sent', ''),
                }
            print(f"[Vector DB] cctv_intents 로드 완료 ({len(intent_map)}개)")
        except Exception as e:
            print(f"[Vector DB] cctv_intents 로드 실패 (summary 단독 검색): {e}")
            for scene in self.scene_data:
                scene['intents'] = {}

        # summary FAISS 인덱스
        summaries = [item.get("summary", "") for item in self.scene_data]
        sum_embeddings = self.model.encode(summaries).astype('float32')
        faiss.normalize_L2(sum_embeddings)
        dimension = sum_embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(sum_embeddings)

        # 의도 문장 FAISS 인덱스 (5가지 의도 문장을 하나로 합쳐 인덱싱)
        intent_texts = [
            " ".join(filter(None, [
                item.get('intents', {}).get('time_sent', ''),
                item.get('intents', {}).get('count_sent', ''),
                item.get('intents', {}).get('action_sent', ''),
                item.get('intents', {}).get('info_sent', ''),
                item.get('intents', {}).get('error_sent', ''),
            ])) or item.get("summary", "")
            for item in self.scene_data
        ]
        intent_embeddings = self.model.encode(intent_texts).astype('float32')
        faiss.normalize_L2(intent_embeddings)
        self.intent_index = faiss.IndexFlatIP(dimension)
        self.intent_index.add(intent_embeddings)

        print(f"[Vector DB] {len(self.scene_data)}개 영상 데이터로 인덱스 구축 완료.")

    def search(self, query: str, top_k: int = 3, intent: Optional[str] = None) -> List[Dict]:
        if self.index is None or not self.scene_data:
            return []

        is_oldest = any(kw in query for kw in OLDEST_KEYWORDS)
        is_newest = any(kw in query for kw in NEWEST_KEYWORDS)
        k_fetch = min(len(self.scene_data), max(top_k * 3, 6) if (is_oldest or is_newest) else max(top_k * 2, 4))

        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)

        # summary 검색
        sum_scores, sum_indices = self.index.search(query_embedding, k_fetch)

        # 의도 문장 검색
        intent_field = intent or _detect_intent_field(query)
        if self.intent_index is not None:
            int_scores, int_indices = self.intent_index.search(query_embedding, k_fetch)
        else:
            int_scores, int_indices = sum_scores, sum_indices

        # 점수 병합: summary 60% + 의도 문장 40%
        score_map: Dict[int, float] = {}
        for i, idx in enumerate(sum_indices[0]):
            if 0 <= idx < len(self.scene_data):
                score_map[idx] = 0.6 * float(sum_scores[0][i])
        for i, idx in enumerate(int_indices[0]):
            if 0 <= idx < len(self.scene_data):
                score_map[idx] = score_map.get(idx, 0.0) + 0.4 * float(int_scores[0][i])

        sorted_indices = sorted(score_map.keys(), key=lambda x: -score_map[x])
        candidates = [self.scene_data[i] for i in sorted_indices[:k_fetch]]

        if is_oldest or is_newest:
            candidates = sorted(
                candidates,
                key=lambda x: x.get("event_date") or "",
                reverse=is_newest
            )

        top_candidates = candidates[:top_k]
        raw_scores = [score_map.get(self.scene_data.index(item) if item in self.scene_data else -1, 0.0) for item in top_candidates]
        max_score = max(raw_scores) if raw_scores else 1.0
        min_score = min(raw_scores) if raw_scores else 0.0
        score_range = max_score - min_score if max_score != min_score else 1.0

        results = []
        for i, item in enumerate(top_candidates):
            idx = self.scene_data.index(item) if item in self.scene_data else -1
            combined_score = score_map.get(idx, 0.0)
            # 결과 내 상대 정규화: 최고점→1.0, 최저점→0.7 범위로 스케일링
            normalized_score = 0.7 + 0.3 * (combined_score - min_score) / score_range
            intents = item.get('intents', {})
            results.append({
                "rank":           i + 1,
                "description":    item.get("summary", ""),
                "video_filename": item.get("video_filename"),
                "event_date":     item.get("event_date"),
                "intent_info":    intents.get(intent_field, ""),
                "score":          round(normalized_score, 4),
                "distance":       round(1 - combined_score, 4),
                "image_path":     None,
                "video_url":      f"/static/mp4Data/{item.get('video_filename', '')}",
            })

        print(f"[Vector DB] {len(results)}개 유사 장면 검색 완료 (summary+intent 혼합).")
        return results

    def reload(self):
        """영상 추가 후 인덱스를 다시 빌드합니다."""
        self._build_index()


# 싱글톤 인스턴스
vector_db_service = VectorDBService()
