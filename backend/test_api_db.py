import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.database import db_service
from database.database import SessionLocal
from database import models

def test_logging_5_times():
    print("--- 검색 API 로깅 테스트 시작 (5회) ---")
    test_queries = [
        ("강아지를 산책시키는 사람", "SEARCH"),
        ("오늘 날씨 어때?", "GENERAL"),
        ("검은색 SUV 차량 조회", "SEARCH"),
        ("안녕 반가워", "GENERAL"),
        ("빨간색 옷을 입은 사람", "SEARCH")
    ]

    for query, intent in test_queries:
        print(f"Logging: '{query}' with intent '{intent}'")
        db_service.log_search(query, intent)

    print("\n--- DB 저장 결과 확인 ---")
    db = SessionLocal()
    logs = db.query(models.SearchLog).all()
    print(f"현재 저장된 로그 개수: {len(logs)}개")
    
    for log in logs[-5:]:
        print(f"ID: {log.id} | Query: {log.query} | Intent: {log.intent} | Time: {log.timestamp}")
    
    db.close()

if __name__ == "__main__":
    test_logging_5_times()
