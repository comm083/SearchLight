import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_search_service import image_search_service

async def test_image_search():
    print("\n[이미지 검색 테스트] Image-to-Image 검색 확인")
    
    # 테스트용 쿼리 이미지 설정 (기존 이미지 중 하나를 쿼리로 사용)
    # 실제로는 사용자가 업로드한 새로운 이미지가 들어옵니다.
    query_image_rel_path = "static/images/thief1.png"
    query_image_path = os.path.join(os.path.dirname(__file__), "..", query_image_rel_path)
    
    if not os.path.exists(query_image_path):
        print(f"[Error] 테스트 이미지를 찾을 수 없습니다: {query_image_path}")
        return

    print(f"쿼리 이미지: {query_image_rel_path}")
    print("유사 이미지 검색 중 (CLIP)...")
    
    # 검색 수행
    results = image_search_service.search(query_image_path, top_k=3)
    
    print(f"\n[검색 결과]")
    for res in results:
        print(f"순위 {res['rank']} | 유사도: {res['similarity']}")
        print(f"  - 설명: {res['description']}")
        print(f"  - 경로: {res['image_path']}")
        print("-" * 30)

    if len(results) > 0 and results[0]['similarity'] > 0.9:
        print("\n[SUCCESS] 성공: 이미지 기반 유사도 검색이 정상적으로 작동합니다.")
    else:
        print("\n[FAIL] 실패: 검색 결과가 없거나 유사도가 너무 낮습니다.")

if __name__ == "__main__":
    asyncio.run(test_image_search())
