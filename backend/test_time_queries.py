from datetime import datetime
from app.services.korean_time_parser import KoreanTimeParser

mock_now = datetime(2026, 4, 28, 21, 0, 0)
parser = KoreanTimeParser(now=mock_now)

test_queries = [
    "오늘 낮에 무슨 일 있었어?",
    "오늘 저녁에 검정색 모자쓴 사람 있었나?",
    "어제 저녁 상황 알려줘"
]

print(f"기준 시각: {mock_now}")
for q in test_queries:
    res = parser.parse(q)
    print(f"\n질의: {q}")
    if res:
        print(f"결과: {res}")
    else:
        print("결과: 파싱 실패")
