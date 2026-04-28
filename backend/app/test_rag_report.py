import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import process_user_query, SearchRequest

async def test_rag_report():
    print("\n[RAG 테스트] 보안 보고서 생성 확인")
    # 요약(SUMMARIZATION) 의도를 유도하는 질문
    req = SearchRequest(query="어제 오후 주차장 상황 요약해서 보고해줘", session_id="rag_test_user")
    
    print(f"질의: {req.query}")
    print("AI 보고서 생성 중... (잠시만 기다려 주세요)")
    
    resp = await process_user_query(req)
    
    print(f"\n[결과]")
    print(f"분류된 의도: {resp['intent_info']['intent']}")
    print(f"메시지: {resp['message']}")
    print(f"검색된 결과 수: {len(resp['results'])}건")
    
    print("\n[AI 생성 보안 보고서]")
    if resp['ai_report']:
        print("-" * 50)
        print(resp['ai_report'])
        print("-" * 50)
        print("\n[SUCCESS] 성공: AI가 검색 결과를 바탕으로 보고서를 생성했습니다.")
    else:
        print("\n[FAIL] 실패: AI 보고서가 생성되지 않았습니다.")

if __name__ == "__main__":
    asyncio.run(test_rag_report())
