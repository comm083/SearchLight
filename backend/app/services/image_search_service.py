import os
import json
import faiss
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

class ImageSearchService:
    def __init__(self):
        print("[Service] Image-to-Image 검색 엔진 초기화 중 (CLIP)...")
        # CLIP 모델 로드: 이미지와 텍스트를 동일한 벡터 공간에 매핑
        self.model = SentenceTransformer('clip-ViT-B-32')
        
        # 경로 설정 (프로젝트 루트: SearchLight/)
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.backend_dir = os.path.join(self.root_dir, 'backend')
        json_path = os.path.join(self.root_dir, 'ai', 'data', 'scene_descriptions.json')
        
        # 데이터 로드
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"[Error] 데이터 로드 실패: {e}")
            self.data = []

        # 이미지 경로가 유효한 데이터만 필터링
        self.valid_items = []
        images = []
        
        print("[Service] 이미지 특징 추출 및 인덱싱 시작...")
        for item in self.data:
            if "image_path" in item:
                # /static/images/... 형태를 시스템 경로로 변환
                rel_path = item["image_path"].lstrip('/')
                full_path = os.path.join(self.backend_dir, rel_path)
                
                if os.path.exists(full_path):
                    try:
                        img = Image.open(full_path).convert('RGB')
                        images.append(img)
                        self.valid_items.append(item)
                    except Exception as e:
                        print(f"[Warning] 이미지 로드 실패 ({full_path}): {e}")

        if images:
            # 이미지 임베딩 생성
            embeddings = self.model.encode(images, batch_size=32, show_progress_bar=True)
            embeddings = np.array(embeddings).astype('float32')
            
            # FAISS 인덱스 생성 (코사인 유사도 검색을 위해 L2 정규화 후 Inner Product 사용)
            faiss.normalize_L2(embeddings)
            self.dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(embeddings)
            
            print(f"[Service] 총 {len(self.valid_items)}개 이미지 인덱싱 완료!")
        else:
            print("[Error] 인덱싱할 이미지가 없습니다.")

    def search(self, query_image_path: str, top_k: int = 3):
        """
        쿼리 이미지를 기반으로 유사한 CCTV 장면을 검색합니다.
        """
        try:
            query_img = Image.open(query_image_path).convert('RGB')
            query_vector = self.model.encode([query_img]).astype('float32')
            faiss.normalize_L2(query_vector)
            
            distances, indices = self.index.search(query_vector, top_k)
            
            results = []
            for i in range(top_k):
                idx = indices[0][i]
                score = float(distances[0][i])
                item = self.valid_items[idx]
                
                results.append({
                    "rank": i + 1,
                    "id": item["id"],
                    "description": item["description"],
                    "image_path": item["image_path"],
                    "similarity": round(score, 4)
                })
            return results
        except Exception as e:
            print(f"[Search Error] 이미지 검색 실패: {e}")
            return []

# 싱글톤 인스턴스 생성
image_search_service = ImageSearchService()
