import requests
import json

def test_search():
    url = "http://localhost:8000/api/search"
    payload = {
        "query": "검은색 옷을 입은 사람",
        "top_k": 3
    }
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Intent: {data.get('intent_info', {}).get('intent')}")
        results = data.get('results', [])
        print(f"Results count: {len(results)}")
        print("-" * 30)
        print("AI Report:")
        print(data.get('ai_report'))
        print("-" * 30)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
