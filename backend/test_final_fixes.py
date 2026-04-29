import requests
import json
from datetime import datetime

def test_suite():
    base_url = "http://localhost:8000/api/search"
    session_id = f"test_{datetime.now().strftime('%H%M%S')}"

    print(f"Starting Test Suite (Session: {session_id})\n")

    # 1. "지금" 시간 파싱 테스트
    print("--- Test 1: '지금' Time Range ---")
    payload = {"query": "지금 정문 상황 알려줘", "session_id": session_id}
    res = requests.post(base_url, json=payload).json()
    print(f"Query: {payload['query']}")
    print(f"Time Range: {res['time_info']}")
    # 예상: 현재 시각 - 1분 ~ 현재 시각
    print(f"Intent: {res['intent_info']['intent']}\n")

    # 2. Localization 전용 라우팅 테스트
    print("--- Test 2: Localization Routing ---")
    payload = {"query": "현재 정문에 누구 있어?", "session_id": session_id}
    res = requests.post(base_url, json=payload).json()
    print(f"Query: {payload['query']}")
    print(f"AI Report: {res['ai_report'][:100]}...")
    print(f"Results Count: {len(res['results'])}")
    # 예상: RAG 보고서가 아닌 실시간 위치 확인 메시지 형식
    print("\n")

    # 3. 대화 맥락 특징 유지 테스트
    print("--- Test 3: Feature Persistence ---")
    # Q1: 특징 주입
    payload = {"query": "빨간 옷 입은 사람 찾아줘", "session_id": session_id}
    print(f"Q1: {payload['query']}")
    requests.post(base_url, json=payload)
    
    # Q2: 지칭어 사용
    payload = {"query": "그 사람 지금 어디 있어?", "session_id": session_id}
    print(f"Q2: {payload['query']}")
    res = requests.post(base_url, json=payload).json()
    # 서버 로그에서 특징 결합 확인 필요 (또는 결과 데이터 확인)
    print(f"Context Used: {res.get('context_used')}")
    print(f"AI Report: {res['ai_report'][:100]}...")
    print("\n")

    # 4. 상세 타임라인 필터링 테스트
    print("--- Test 4: Timeline Filtering ---")
    payload = {"query": "오늘 오전 10시 상황 요약해줘", "session_id": session_id}
    res = requests.post(base_url, json=payload).json()
    print(f"Query: {payload['query']}")
    print(f"Requested Time: {res['time_info']['start_time']} ~ {res['time_info']['end_time']}")
    
    if res['results']:
        detections = res['results'][0].get('detections', [])
        print(f"Detections Count: {len(detections)}")
        if detections:
            print(f"First Detection Time: {detections[0]['time']}")
            # 예상: 모든 감지 시간이 오전 10시~11시 사이여야 함
    print("\n")

if __name__ == "__main__":
    test_suite()
