import os
import sys
import random
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def seed_data():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    print("[Seed] 100개의 실감 나는 시나리오 데이터 생성을 시작합니다...")

    # 시나리오 1: 무인 상점 사장님 (Store Owner)
    store_queries = [
        "어제 밤 12시 이후에 술 취한 사람 있었어?",
        "카운터 근처에서 서성거리는 사람 찾아줘",
        "누가 담배 진열대 앞에서 오래 머물렀니?",
        "결제 안 하고 나간 사람 있는 것 같아, 확인해줘",
        "아르바이트생 어제 몇 시에 퇴근했어?",
        "지금 매장 안에 사람 몇 명 있어?",
        "어제 새벽에 문 안 닫고 간 사람 누구야?",
        "매장 입구에 쓰레기 버리고 간 사람 찾아줘",
        "어제 오후 3시경에 발생한 결제 오류 상황 보여줘",
        "수상한 행동을 하는 사람이 감지되었니?"
    ]

    # 시나리오 2: 아파트 경비원 (Apartment Security)
    apt_queries = [
        "어제 밤에 소방차 전용 구역에 주차한 차 누구야?",
        "지하 주차장 2층에서 서성거리는 사람 있었어?",
        "놀이터에서 밤 늦게 소란 피운 애들 찾아줘",
        "택배함 근처에서 수상한 행동 한 사람 있어?",
        "어제 오후에 103동 입구 화단에 쓰레기 버린 사람 누구니?",
        "공동현관 비밀번호 계속 틀린 사람 확인해줘",
        "옥상 출입문 열린 적 있었어?",
        "엘리베이터 안에서 흡연한 사람 찾아줘",
        "어제 외부 차량이 주차장에 들어온 기록 보여줘",
        "순찰 중에 발견된 이상 징후 있었니?"
    ]

    intents = ["SUMMARIZATION", "BEHAVIORAL", "LOCALIZATION", "COUNTING", "CAUSAL"]
    severities = ["INFO", "WARNING", "EMERGENCY"]
    alert_types = ["THEFT", "VIOLENCE", "FIRE", "LOITERING", "INTRUSION"]

    # 1. search_logs 50건 생성
    print("--- 'search_logs' 50건 생성 중...")
    for i in range(50):
        scenario = random.choice(["owner", "guard"])
        query = random.choice(store_queries if scenario == "owner" else apt_queries)
        
        # 무작위 과거 시간 생성
        past_time = datetime.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
        
        data = {
            "query": query,
            "intent": random.choice(intents),
            "ai_report": f"AI 분석 결과, {past_time.strftime('%m월 %d일 %H시')}경에 해당 상황이 감지되었습니다. 상세 영상을 확인하십시오.",
            "session_id": f"session_{random.randint(1000, 9999)}",
            "user_type": scenario,
            "created_at": past_time.isoformat()
        }
        supabase.table('search_logs').insert(data).execute()

    # 2. alerts 50건 생성
    print("--- 'alerts' 50건 생성 중...")
    for i in range(50):
        scenario = random.choice(["owner", "guard"])
        alert_type = random.choice(alert_types)
        
        past_time = datetime.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
        
        alert_data = {
            "type": alert_type,
            "severity": random.choice(severities),
            "description": f"[{'무인상점' if scenario=='owner' else '아파트'}] {alert_type} 상황이 감지되었습니다. 즉시 확인 바랍니다.",
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "created_at": past_time.isoformat()
        }
        supabase.table('alerts').insert(alert_data).execute()

    print("\n✨ 모든 테스트 데이터(100건)가 성공적으로 업로드되었습니다!")

if __name__ == "__main__":
    seed_data()
