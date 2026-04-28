import sys
import os
import json

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ood_handling():
    url = "http://localhost:8000/api/search"
    
    test_queries = [
        "안녕? 반가워",
        "오늘 날씨 어때?",
        "배고픈데 맛집 추천해줘",
        "너 이름이 뭐야?"
    ]
    
    print("\n[일상 질의 예외 처리(OOD) 테스트 시작]")
    
    for query in test_queries:
        print(f"\n[질문]: {query}")
        payload = {
            "query": query,
            "session_id": "ood_test_session"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"[의도]: {result['intent_info']['intent']}")
                print(f"[답변]: {result.get('answer', '응답 없음')}")
                
                if result['intent_info']['intent'] == "CHITCHAT":
                    print("✅ 성공: 일상 질의로 판별되어 적절한 거절 메시지가 생성되었습니다.")
                else:
                    print("❌ 실패: 일상 질의로 판별되지 않았습니다.")
            else:
                print(f"❌ 에러: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    # 서버가 실행 중이어야 합니다.
    # 여기서는 직접 함수를 호출하는 방식으로 테스트하려면 main.py의 로직을 import해야 함.
    # 하지만 실제 API 동작을 확인하기 위해 requests를 사용함.
    # 서버 실행 중이 아닐 경우를 대비해 Mocking 또는 직접 호출 로직을 작성할 수 있음.
    
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    print("\n[일상 질의 예외 처리(OOD) 로컬 테스트 시작]")
    
    test_queries = [
        "안녕? 반가워",
        "오늘 날씨 어때?",
        "배고픈데 맛집 추천해줘",
        "너 이름이 뭐야?"
    ]
    
    for query in test_queries:
        print(f"\n[질문]: {query}")
        response = client.post("/api/search", json={"query": query, "session_id": "test_session"})
        result = response.json()
        print(f"[의도]: {result['intent_info']['intent']}")
        print(f"[답변]: {result.get('answer', '응답 없음')}")
        
        if result['intent_info']['intent'] == "CHITCHAT":
            print("✅ 성공: 일상 질의로 판별되어 적절한 거절 메시지가 생성되었습니다.")
        else:
            print("❌ 실패: 일상 질의로 판별되지 않았습니다.")
