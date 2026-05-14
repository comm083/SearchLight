import urllib.request, json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

payload = json.dumps({"query":"빨간 옷", "session_id":"12345", "top_k": 3}).encode('utf-8')
req = urllib.request.Request(
    'http://localhost:8000/api/search',
    data=payload,
    headers={'Content-Type':'application/json'}
)
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    print(f"Results Count: {len(data.get('results', []))}")
    for i, item in enumerate(data.get('results', [])):
        print(f"[{i+1}] {item.get('video_filename')} -> clip_url: {item.get('clip_url')}")
except Exception as e:
    print(e)
