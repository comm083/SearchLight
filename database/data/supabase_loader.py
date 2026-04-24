import random
from datetime import datetime, timedelta
from supabase import create_client, Client

# 사용자님이 설정하신 Supabase 정보
URL = "https://nnuetzqcbnnkarzuqaeh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5udWV0enFjYm5ua2FyenVxYWVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwMDczODAsImV4cCI6MjA5MjU4MzM4MH0.kp6qof8vnlORn6Doluydsaatwm3y4QuAqMleYtteyEo"

supabase: Client = create_client(URL, KEY)

def generate_virtual_data(count=480):
    label_desc_map = {
        "person": ["검은색 옷을 입은 사람이 골목을 지나감", "수상한 인물이 건물 주변을 배회함", "파란색 셔츠를 입은 남자가 가방을 들고 있음"],
        "car": ["흰색 SUV 차량이 주행 중", "빨간색 승용차가 신호를 위반함", "검은색 세단이 주차장에 진입함"],
        "bicycle": ["자전거를 탄 사람이 횡단보도를 건너는 중", "공유 자전거를 이용하는 시민이 포착됨"],
        "motorcycle": ["배달 오토바이가 인도를 주행함", "헬멧을 쓰지 않은 오토바이 운전자가 감지됨"],
        "truck": ["트럭이 짐을 싣고 이동 중", "대형 화물차가 골목 입구에 정차함"]
    }
    
    camera_ids = ["CAM-001", "CAM-002", "CAM-003", "CAM-004", "CAM-005"]
    labels = list(label_desc_map.keys())

    events = []
    current_time = datetime.now()

    for i in range(count):
        timestamp = (current_time - timedelta(minutes=random.randint(1, 2400))).isoformat()
        label = random.choice(labels)
        camera_id = random.choice(camera_ids)
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

def run_migration():
    print(f"Supabase로 마이그레이션 시작...")
    data = generate_virtual_data(480)
    
    # 100건씩 끊어서 업로드 (배치 처리)
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            response = supabase.table('yolo_events').insert(batch).execute()
            print(f"{i + len(batch)}개 데이터 업로드 완료...")
        except Exception as e:
            print(f"오류 발생: {e}")
            break

    print("모든 데이터가 Supabase 클라우드로 이전되었습니다!")

if __name__ == "__main__":
    run_migration()
