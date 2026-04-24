from sqlalchemy.orm import Session
from . import models
from datetime import datetime

def get_events_by_time(db: Session, start_time: datetime, end_time: datetime):
    """
    시작 시간과 종료 시간 사이의 이벤트를 분 단위 정밀도로 조회합니다.
    """
    return db.query(models.YoloEvent).filter(
        models.YoloEvent.timestamp >= start_time,
        models.YoloEvent.timestamp <= end_time
    ).all()

def create_events_batch(db: Session, events: list):
    """
    여러 이벤트를 한 번에 삽입합니다.
    """
    db_events = [models.YoloEvent(**event) for event in events]
    db.add_all(db_events)
    db.commit()
    return len(db_events)

def create_search_log(db: Session, query: str, intent: str):
    """
    사용자의 검색 쿼리와 시스템이 판별한 의도를 로그로 기록합니다.
    """
    db_log = models.SearchLog(query=query, intent=intent)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
