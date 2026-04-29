import os
import sys
import random
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def seed_advanced_data():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    print("[Seed] 야간 및 특수 상황 심화 데이터 생성을 시작합니다...")

    # 시나리오: 야간 근무 및 특수 상황 (Night & Special Cases)
    advanced_queries = [
        "새벽 3시경에 매장 주변을 손전등으로 비추던 사람 있었어?",
        "어제 폭우 올 때 지하 주차장에 물 고인 곳 확인해줘",
        "야간에 마스크랑 모자 깊게 눌러쓰고 들어온 사람 찾아줘",
        "매장 구석에서 쓰러진 사람 같은 행동 감지된 적 있니?",
        "새벽에 잠긴 뒷문을 강제로 열려고 한 기록 보여줘",
        "술 취한 사람이 매장 기물을 파손한 상황이 있었어?",
        "폭설로 인해 외부 비상 계단이 미끄러워 보이는 상황이야?",
        "야간 순찰 중에 불이 꺼진 구역에서 움직임이 감지되었니?",
        "어제 새벽에 헬멧을 쓴 오토바이 운전자가 오래 머물렀어?",
        "갑자기 사람이 쓰러지거나 주저앉은 응급 상황 확인해줘"
    ]

    alert_scenarios = [
        {"type": "EMERGENCY", "desc": "야간 구역 내 쓰러진 인물 감지 (응급 상황 의심)"},
        {"type": "INTRUSION", "desc": "새벽 시간대 비인가 구역 강제 진입 시도 감지"},
        {"type": "VANDALISM", "desc": "주차장 내 차량 기물 파손 행위 실시간 감지"},
        {"type": "WEATHER", "desc": "폭우로 인한 배수구 역류 및 침수 위험 감지"},
        {"type": "LOITERING", "desc": "야간 외곽 담벼락 인근 30분 이상 배회자 감지"}
    ]

    # 1. search_logs 25건 추가
    print("--- 야간/심화 'search_logs' 25건 생성 중...")
    for i in range(25):
        query = random.choice(advanced_queries)
        # 주로 새벽 시간대로 설정 (00시 ~ 05시)
        past_time = datetime.now() - timedelta(days=random.randint(0, 5))
        past_time = past_time.replace(hour=random.randint(0, 5), minute=random.randint(0, 59))
        
        data = {
            "query": query,
            "intent": "BEHAVIORAL",
            "ai_report": f"AI 야간 정밀 분석 결과, {past_time.strftime('%H시 %M분')}경 저조도 환경에서 수상한 움직임이 포착되었습니다.",
            "session_id": f"night_session_{random.randint(1000, 9999)}",
            "user_type": "guard",
            "created_at": past_time.isoformat()
        }
        supabase.table('search_logs').insert(data).execute()

    # 2. alerts 25건 추가
    print("--- 야간/응급 'alerts' 25건 생성 중...")
    for i in range(25):
        scenario = random.choice(alert_scenarios)
        past_time = datetime.now() - timedelta(days=random.randint(0, 5))
        past_time = past_time.replace(hour=random.randint(22, 23) if i%2==0 else random.randint(0, 4))
        
        alert_data = {
            "type": scenario["type"],
            "severity": "EMERGENCY" if scenario["type"] in ["EMERGENCY", "INTRUSION"] else "WARNING",
            "description": f"[야간특수] {scenario['desc']}",
            "confidence": round(random.uniform(0.85, 0.99), 2),
            "created_at": past_time.isoformat()
        }
        supabase.table('alerts').insert(alert_data).execute()

    print("\n[SUCCESS] 야간 및 특수 상황 데이터 50건이 추가되었습니다.")

if __name__ == "__main__":
    seed_advanced_data()
