import io
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer


class ClipObjectService:
    """
    CLIP(ViT-B/32) 기반 크롭 객체 임베딩 및 유사 검색 서비스.
    makeJsonData.py 파이프라인에서 저장한 cropped_objects 테이블을 대상으로 한다.
    """

    def __init__(self):
        print("[Service] CLIP 객체 검색 엔진 초기화 중 (clip-ViT-B-32)...")
        self.model = SentenceTransformer('clip-ViT-B-32')
        print("[Service] CLIP 객체 검색 엔진 준비 완료")

    # ──────────────────────────────────────────────
    # 인코딩
    # ──────────────────────────────────────────────

    def encode_image(self, pil_image: Image.Image) -> list:
        """PIL 이미지 → CLIP 임베딩 벡터 (list[float], dim=512)"""
        vec = self.model.encode([pil_image], convert_to_numpy=True)
        return vec[0].tolist()

    def encode_image_bytes(self, image_bytes: bytes) -> list:
        """바이트 → CLIP 임베딩 벡터"""
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        return self.encode_image(img)

    def encode_text(self, text: str) -> list:
        """텍스트 → CLIP 임베딩 벡터 (이미지와 동일 공간)"""
        vec = self.model.encode([text], convert_to_numpy=True)
        return vec[0].tolist()

    # ──────────────────────────────────────────────
    # Supabase pgvector 검색
    # ──────────────────────────────────────────────

    def search(self, query_vector: list, top_k: int = 5, threshold: float = 0.4) -> list:
        """
        pgvector RPC 함수 `match_cropped_objects`를 호출하여 유사 객체를 검색합니다.

        Supabase SQL Editor에서 아래 함수를 미리 생성해야 합니다:

        CREATE OR REPLACE FUNCTION match_cropped_objects(
            query_embedding vector(512),
            match_threshold  float,
            match_count      int
        )
        RETURNS TABLE (
            id            uuid,
            event_id      uuid,
            video_filename text,
            timestamp     timestamptz,
            object_class  text,
            bbox          jsonb,
            image_url     text,
            similarity    float
        )
        LANGUAGE sql STABLE AS $$
            SELECT id, event_id, video_filename, timestamp, object_class, bbox, image_url,
                   1 - (clip_vector <=> query_embedding) AS similarity
            FROM   cropped_objects
            WHERE  1 - (clip_vector <=> query_embedding) > match_threshold
            ORDER  BY clip_vector <=> query_embedding
            LIMIT  match_count;
        $$;
        """
        try:
            from app.services.database import db_service
            if not db_service.supabase:
                return []
            result = db_service.supabase.rpc('match_cropped_objects', {
                'query_embedding': query_vector,
                'match_threshold': threshold,
                'match_count': top_k,
            }).execute()
            return result.data or []
        except Exception as e:
            print(f"[CLIP Search Error] {e}")
            return []

    def search_by_image(self, pil_image: Image.Image, top_k: int = 5) -> list:
        vec = self.encode_image(pil_image)
        return self.search(vec, top_k=top_k)

    def search_by_text(self, text: str, top_k: int = 5) -> list:
        vec = self.encode_text(text)
        return self.search(vec, top_k=top_k)


# 싱글톤 — 서버 기동 시 한 번만 로드
clip_object_service = ClipObjectService()
