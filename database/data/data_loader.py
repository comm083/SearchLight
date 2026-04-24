import sys
import os
import random
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 path에 추가하여 모듈 참조 가능하게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import SessionLocal
from database import crud

def generate_virtual_data(count=480):
    # 라벨별 가능한 상세 설명 매핑
    label_desc_map = {
        "person": [
            "검은색 옷을 입은 사람이 골목을 지나감",
            "수상한 인물이 건물 주변을 배회함",
            "파란색 셔츠를 입은 남자가 가방을 들고 있음"
        ],
        "car": [
            "흰색 SUV 차량이 주행 중",
            "빨간색 승용차가 신호를 위반함",
            "검은색 세단이 주차장에 진입함"
        ],
        "bicycle": [
            "자전거를 탄 사람이 횡단보도를 건너는 중",
            "공유 자전거를 이용하는 시민이 포착됨"
        ],
        "motorcycle": [
            "배달 오토바이가 인도를 주행함",
            "헬멧을 쓰지 않은 오토바이 운전자가 감지됨"
        ],
        "truck": [
            "트럭이 짐을 싣고 이동 중",
            "대형 화물차가 골목 입구에 정차함"
        ]
    }
    
    camera_ids = ["CAM-001", "CAM-002", "CAM-003", "CAM-004", "CAM-005"]
    labels = list(label_desc_map.keys())

    events = []
    current_time = datetime.now()

    for i in range(count):
        timestamp = current_time - timedelta(minutes=random.randint(1, 2400))
        label = random.choice(labels)
        camera_id = random.choice(camera_ids)
        
        # 선택된 라벨에 맞는 설명 중 하나를 선택
        matched_desc = random.choice(label_desc_map[label])
        description = f"{camera_id}: {matched_desc}"
        
        events.append({
            "camera_id": camera_id,
            "label": label,
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "timestamp": timestamp,
            "description": description
        })
    
    return events

def run_loader():
    db = SessionLocal()
    try:
        print(f"Generating 480 virtual events...")
        events_data = generate_virtual_data(480)
        
        print("Inserting data into database...")
        inserted_count = crud.create_events_batch(db, events_data)
        print(f"Successfully inserted {inserted_count} events.")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_loader()
