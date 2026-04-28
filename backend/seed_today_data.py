import asyncio
import os
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

async def seed_today_data():
    print("Starting data generation for today (2026-04-28)...")
    
    # 1. Supabase 연결
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    # 2. 모델 로드
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    
    today_str = "2026-04-28"
    today_events = [
        {"desc": "오전 09:15, 정문 로비를 통해 외부 방문객 3명 입장 확인 (세미나 참석용)", "img": "/static/images/cctv_1.jpg"},
        {"desc": "오전 10:30, 카페테리아 구역 인원 밀집도 상승 (약 15명 체류 중)", "img": "/static/images/cctv_2.jpg"},
        {"desc": "오전 11:45, 배달 오토바이가 정문 앞 소방 구역에 일시 정차 후 이동", "img": "/static/images/cctv_3.jpg"},
        {"desc": "오후 13:20, 검은색 정장을 입은 남성이 3층 대회의실로 입장하는 모습 포착", "img": "/static/images/cctv_4.jpg"},
        {"desc": "오후 14:10, 서쪽 주차장에서 흰색 차량(12가 3456) 출차 확인", "img": "/static/images/cctv_5.jpg"},
        {"desc": "오후 15:05, 하역장 부근에서 물품 하차 작업 중인 작업자 2명 감지", "img": "/static/images/cctv_6.jpg"},
        {"desc": "오후 15:45, 엘리베이터 2호기 내부 청소 작업 진행 중", "img": "/static/images/cctv_7.jpg"},
        {"desc": "오후 16:10, 뒷문 보안 게이트를 통해 직원 1명 정상 퇴근 확인", "img": "/static/images/cctv_8.jpg"},
        {"desc": "오후 16:30, 옥상 정원 구역 배회자 1명 확인 (특이사항 없음)", "img": "/static/images/cctv_9.jpg"},
        {"desc": "오후 16:45, 현재 정문 보안 데스크 인근 유동 인원 2명 포착", "img": "/static/images/cctv_10.jpg"}
    ]

    for i, event in enumerate(today_events):
        event_time = f"{today_str} {9 + (i // 4):02d}:{(i % 4) * 15:02d}:00"
        content = f"[{event_time}] {event['desc']}"
        embedding = model.encode(content).tolist()
        
        metadata = {
            "timestamp": event_time,
            "location": "전체 구역",
            "image_path": event["img"],
            "description": event["desc"]
        }
        
        try:
            supabase.table('cctv_vectors').insert({
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            }).execute()
            print(f"Done: {event_time}")
        except Exception as e:
            print(f"Error at {event_time}: {e}")

    print("\nSuccess! 10 events for today have been inserted.")

if __name__ == "__main__":
    asyncio.run(seed_today_data())
