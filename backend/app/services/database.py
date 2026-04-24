from database.database import SessionLocal
from database import crud

class DBService:
    def __init__(self):
        print("[Service] SQLAlchemy DB 엔진 연동 완료!")

    def log_search(self, query: str, intent: str):
        """
        검색 로그를 데이터베이스에 기록합니다.
        """
        db = SessionLocal()
        try:
            return crud.create_search_log(db, query=query, intent=intent)
        finally:
            db.close()

# 싱글톤 패턴
db_service = DBService()
