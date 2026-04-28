import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import simulate_realtime_event

async def test_active_alerting():
    print("\n[실시간 알림 테스트] 이상 행동 감지 시뮬레이션")
    
    # 시나리오 1: 정상적인 상황 (사람이 걷고 있음)
    print("\n[시나리오 1] 일반적인 상황")
    event1 = "사람이 복도를 걸어가고 있습니다."
    resp1 = await simulate_realtime_event(description=event1)
    print(f"상황: {event1}")
    print(f"결과: {resp1['message']}")
    
    # 시나리오 2: 방화 상황
    print("\n[시나리오 2] 방화 상황 감지")
    event2 = "진열대 구석에서 한 남성이 라이터로 불을 붙이려 하고 있습니다."
    resp2 = await simulate_realtime_event(description=event2)
    print(f"상황: {event2}")
    if resp2['status'] == 'alert':
        print(f"결과: {resp2['data']['title']} - {resp2['data']['message']}")
    else:
        print(f"결과: {resp2['message']}")
    
    # 시나리오 3: 폭행 상황
    print("\n[시나리오 3] 폭행 상황 감지")
    event3 = "두 남성이 서로 멱살을 잡고 때리며 싸우고 있습니다."
    resp3 = await simulate_realtime_event(description=event3)
    print(f"상황: {event3}")
    if resp3['status'] == 'alert':
        print(f"결과: {resp3['data']['title']} - {resp3['data']['message']}")
    else:
        print(f"결과: {resp3['message']}")
    
    # 시나리오 4: 절도 상황
    print("\n[시나리오 4] 절도 상황 감지")
    event4 = "모자를 쓴 사람이 가방에 물건을 몰래 넣고 있습니다."
    resp4 = await simulate_realtime_event(description=event4)
    print(f"상황: {event4}")
    if resp4['status'] == 'alert':
        print(f"결과: {resp4['data']['title']} - {resp4['data']['message']}")
    else:
        print(f"결과: {resp4['message']}")
    
    if all(r['status'] == 'alert' for r in [resp2, resp3, resp4]):
        print("\n[SUCCESS] 성공: 무인 편의점 3대 주요 범죄 상황을 모두 실시간 감지했습니다.")
    else:
        print("\n[FAIL] 실패: 일부 위험 상황을 감지하지 못했습니다.")

if __name__ == "__main__":
    asyncio.run(test_active_alerting())
