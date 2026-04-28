import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_db_service import vector_db_service
from app.services.nlp_service import nlp_service

async def test_cloud_rag():
    print("\n[Cloud Native RAG 테스트] Supabase Vector DB 연동 확인")
    
    # 1. 클라우드 검색 테스트
    query = "빨간 옷 입은 사람 찾아줘"
    print(f"\n[Step 1] 클라우드 검색 시도: '{query}'")
    
    search_results = vector_db_service.search(query, top_k=3)
    
    if search_results:
        print(f"[SUCCESS] 검색 성공! {len(search_results)}개의 관련 장면을 찾았습니다.")
        for i, res in enumerate(search_results):
            print(f"   {i+1}. {res['description']} (유사도: {res['score']:.4f})")
            
        # 2. RAG 보고서 생성 테스트
        print("\n[Step 2] 검색 결과를 바탕으로 AI 보안 보고서 생성 중...")
        report = nlp_service.generate_security_report(query, search_results)
        print("-" * 50)
        print(f"AI 보고서:\n{report}")
        print("-" * 50)
        print("\n[FINISH] 결과: 로컬 파일 없이 클라우드 데이터만으로 RAG가 완벽하게 작동합니다!")
    else:
        print("❌ 검색 결과가 없습니다. 데이터 마이그레이션 및 match_cctv_vectors 함수를 확인하세요.")

if __name__ == "__main__":
    asyncio.run(test_cloud_rag())
