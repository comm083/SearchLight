import sys
import os
from datetime import datetime

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import process_user_query, SearchRequest

async def test_multiturn():
    session_id = "test_user_123"
    
    print("\n[테스트 1] 첫 번째 질문 (시간/장소 명시)")
    req1 = SearchRequest(query="어제 오후 2시 주차장에 누구 있었어?", session_id=session_id)
    resp1 = await process_user_query(req1)
    print(f"질의: {req1.query}")
    print(f"의도: {resp1['intent_info']['intent']}")
    print(f"시간: {resp1['time_info']['raw']} ({resp1['time_info']['start_time']} ~ {resp1['time_info']['end_time']})")
    print(f"컨텍스트 사용 여부: {resp1['context_used']}")
    
    print("\n[테스트 2] 두 번째 질문 (지칭어 사용)")
    # "그때" -> 어제 오후 2시 기억해야 함
    req2 = SearchRequest(query="그때 거기 사람 몇 명이야?", session_id=session_id)
    resp2 = await process_user_query(req2)
    print(f"질의: {req2.query}")
    print(f"의도: {resp2['intent_info']['intent']}")
    print(f"시간: {resp2['time_info']['raw']} ({resp2['time_info']['start_time']} ~ {resp2['time_info']['end_time']})")
    print(f"컨텍스트 사용 여부: {resp2['context_used']}")
    
    if resp2['time_info']['start_time'] == resp1['time_info']['start_time']:
        print("\n[SUCCESS] 성공: 이전 대화의 시간을 성공적으로 계승했습니다.")
    else:
        print("\n[FAIL] 실패: 시간 계승이 이루어지지 않았습니다.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_multiturn())
