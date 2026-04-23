import sqlite3
import datetime

def run_sqlite_test():
    print("1. SQLite 데이터베이스 연결 및 테이블 생성 중...")
    # 파일 형태의 가벼운 데이터베이스인 test_events.db에 연결 (없으면 자동 생성됨)
    conn = sqlite3.connect("test_events.db")
    cursor = conn.cursor()

    # 테스트를 위해 기존에 테이블이 있다면 삭제
    cursor.execute("DROP TABLE IF EXISTS cctv_events")

    # 이벤트 로그를 저장할 구조(테이블) 생성 (ID, 카메라번호, 탐지시간, 상세설명)
    cursor.execute("""
        CREATE TABLE cctv_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT,
            timestamp DATETIME,
            description TEXT
        )
    """)

    print("\n2. CCTV 탐지 이벤트 데이터 삽입 (저장) 중...")
    # 시간에 맞춰 발생한 테스트용 더미 데이터
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    events = [
        ("CAM-01", current_time, "빨간색 패딩을 입은 남자가 골목길을 급하게 뛰어감"),
        ("CAM-02", current_time, "검은색 세단이 신호를 위반하고 교차로를 지나감"),
        ("CAM-03", current_time, "파란색 모자를 쓴 사람이 자전거를 타고 횡단보도를 건넘")
    ]

    # 데이터베이스에 여러 개의 데이터를 한 번에 삽입 (Insert)
    cursor.executemany("""
        INSERT INTO cctv_events (camera_id, timestamp, description) 
        VALUES (?, ?, ?)
    """, events)
    
    # 데이터베이스에 변경사항 영구 저장(Commit)
    conn.commit()
    print("-> 3개의 데이터가 성공적으로 DB에 저장되었습니다.")

    print("\n3. 저장된 데이터 조회(조회 쿼리) 테스트...")
    # 저장된 모든 데이터를 가져오기
    cursor.execute("SELECT * FROM cctv_events")
    rows = cursor.fetchall()

    print("\n=== SQLite 저장된 CCTV 이벤트 목록 ===")
    for row in rows:
        print(f"[{row[0]}] 카메라: {row[1]} | 시간: {row[2]}")
        print(f"      -> 내용: {row[3]}\n")

    # 데이터베이스 연결 종료
    conn.close()

if __name__ == "__main__":
    run_sqlite_test()
