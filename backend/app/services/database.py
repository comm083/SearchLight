import sqlite3
import datetime

class SQLiteService:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        print(f"[Service] SQLite DB({self.db_path}) 초기화 중...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 사용자의 검색 기록을 저장하는 통합 로그 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                intent TEXT,
                timestamp DATETIME
            )
        """)
        conn.commit()
        conn.close()
        print("[Service] SQLite DB 연동 완료!")

    def log_search(self, query: str, intent: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO search_logs (query, intent, timestamp)
            VALUES (?, ?, ?)
        """, (query, intent, current_time))
        
        conn.commit()
        conn.close()

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
db_service = SQLiteService()
