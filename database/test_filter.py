from database.database import SessionLocal
from database import crud
from datetime import datetime, timedelta

def test_time_filtering():
    db = SessionLocal()
    try:
        # 최근 1시간 동안의 데이터 조회 테스트
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        print(f"Testing filter from {start_time} to {end_time}...")
        events = crud.get_events_by_time(db, start_time, end_time)
        
        print(f"Found {len(events)} events in the last hour.")
        if len(events) > 0:
            for event in events[:3]: # 상위 3개만 출력
                print(f" - [{event.timestamp}] {event.label}: {event.description}")
        
        # 정밀 필터링 테스트 (예: 특정 10분 구간)
        precise_start = end_time - timedelta(minutes=30)
        precise_end = end_time - timedelta(minutes=20)
        print(f"\nTesting precise filter from {precise_start} to {precise_end}...")
        precise_events = crud.get_events_by_time(db, precise_start, precise_end)
        print(f"Found {len(precise_events)} events in that 10-minute window.")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_time_filtering()
