import urllib.request, json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

req = urllib.request.Request(
    'http://localhost:8000/api/search',
    data=b'{"query":"test", "session_id":"123", "top_k": 3}',
    headers={'Content-Type':'application/json'}
)
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    print("Clip URLs:")
    for item in data['results']:
        print("-", item.get('clip_url'))
except Exception as e:
    print(e)
