import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_search_and_history():
    session_id = "test_user_123"
    
    # 1. 검색 수행
    print(f"--- Searching for session: {session_id} ---")
    search_data = {
        "query": "검정색 옷을 입은 사람",
        "session_id": session_id,
        "top_k": 1
    }
    res = requests.post(f"{BASE_URL}/search", json=search_data)
    print("Search Response: [Received]")
    
    # 2. 히스토리 조회
    print(f"\n--- Fetching history for session: {session_id} ---")
    res = requests.get(f"{BASE_URL}/history/{session_id}")
    history_data = res.json()
    print(f"History Count: {len(history_data.get('history', []))}")
    
    if history_data["status"] == "success" and len(history_data["history"]) > 0:
        print("\n[SUCCESS] History persistence verified!")
    else:
        print("\n[FAILURE] History not found.")

if __name__ == "__main__":
    test_search_and_history()
