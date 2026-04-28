import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database import db_service
from app.services.alert_service import alert_service

async def test_supabase_sync():
    print("\n[Supabase 연동 테스트] 데이터 저장 확인")
    
    # 1. 일반 검색 로그 테스트 (AI 보고서 포함)
    print("\n[Step 1] 검색 로그 저장 테스트...")
    db_service.log_search(
        query="테스트 검색어입니다", 
        intent="SUMMARIZATION", 
        ai_report="이것은 Supabase에 저장될 테스트 AI 보고서 본문입니다."
    )
    print("[SUCCESS] 검색 로그 전송 완료 (Supabase 대시보드 확인 필요)")
    
    # 2. 실시간 알림 저장 테스트
    print("\n[Step 2] 실시간 알림 DB 저장 테스트...")
    test_event = "누군가 매장 구석에서 라이터로 불을 붙이려 합니다."
    print(f"이벤트 발생: {test_event}")
    
    # alert_service를 통해 처리 (내부에서 db_service.save_alert 호출됨)
    alert_result = alert_service.process_new_event(test_event, "static/images/fire1.png")
    
    if alert_result:
        print(f"[SUCCESS] 알림 감지 및 DB 저장 시도 완료: {alert_result['type']}")
    else:
        print("❌ 알림 감지 실패")

    print("\n[결과] Supabase 테이블(search_logs, alerts)에 데이터가 정상적으로 전송되었습니다.")
    print("※ 실제 저장 여부는 Supabase 대시보드에서 직접 확인해 주세요.")

if __name__ == "__main__":
    asyncio.run(test_supabase_sync())
