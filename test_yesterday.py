import json, urllib.request

req = urllib.request.Request(
    'http://localhost:8000/api/search',
    data=json.dumps({"query":"어제 무슨 일 있었어", "session_id":"12345", "top_k": 5}).encode('utf-8'),
    headers={'Content-Type':'application/json'}
)
res = urllib.request.urlopen(req)
data = json.loads(res.read())

print("Time Info from parser:", data.get('time_info'))
for item in data.get('results', []):
    print(f"File: {item.get('video_filename')} | Date: {item.get('event_date')}")
