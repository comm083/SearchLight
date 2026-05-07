"""
cctv_vectors 테이블의 content와 metadata를
편의점 CCTV 시나리오에 맞게 업데이트하는 스크립트
"""
import random
from app.services.database import db_service

supabase = db_service.supabase

# ── 편의점 구역 목록 ──────────────────────────────────────
LOCATIONS = [
    "계산대", "음료 냉장고", "과자 진열대", "입구", "출구",
    "주류 코너", "즉석식품 코너", "화장실 앞", "ATM 앞", "주차장"
]

# ── 편의점 시나리오 템플릿 ────────────────────────────────
# (content, location, tag) 형태. tag: 'Person' or 'Vehicle'
SCENARIOS = [
    # 일반 고객 행동
    ("손님이 음료 냉장고 앞에서 제품을 고르고 있습니다.", "음료 냉장고", "Person"),
    ("20대 남성 손님이 과자 진열대를 훑어보고 있습니다.", "과자 진열대", "Person"),
    ("여성 손님이 계산대에서 카드로 결제를 진행 중입니다.", "계산대", "Person"),
    ("학생으로 보이는 손님이 즉석식품 코너에서 컵라면을 고르고 있습니다.", "즉석식품 코너", "Person"),
    ("손님 2명이 나란히 입구로 들어오고 있습니다.", "입구", "Person"),
    ("손님이 ATM에서 현금을 인출하고 있습니다.", "ATM 앞", "Person"),
    ("중년 남성이 주류 코너에서 맥주를 확인하고 있습니다.", "주류 코너", "Person"),
    ("손님이 계산 후 영수증을 받고 출구로 나가고 있습니다.", "출구", "Person"),
    ("어린이를 동반한 보호자가 과자 진열대 앞에 서 있습니다.", "과자 진열대", "Person"),
    ("손님이 음료 냉장고 문을 열고 음료를 꺼내고 있습니다.", "음료 냉장고", "Person"),
    # 직원 행동
    ("직원이 진열대 상품을 정리하고 있습니다.", "과자 진열대", "Person"),
    ("직원이 계산대 앞에서 대기 중입니다.", "계산대", "Person"),
    ("직원이 즉석식품 코너 조리기를 점검하고 있습니다.", "즉석식품 코너", "Person"),
    ("직원이 음료 냉장고에 새 제품을 채워 넣고 있습니다.", "음료 냉장고", "Person"),
    ("직원이 입구 바닥을 청소하고 있습니다.", "입구", "Person"),
    # 주의 상황
    ("모자를 눌러쓴 남성이 주류 코너 근처에서 장시간 서성이고 있습니다.", "주류 코너", "Person"),
    ("손님이 계산대를 통과하지 않고 출구 방향으로 빠르게 이동 중입니다.", "출구", "Person"),
    ("10대로 보이는 청소년이 주류 코너에 접근하고 있습니다.", "주류 코너", "Person"),
    ("화장실 앞에서 낯선 남성이 오랜 시간 대기 중입니다.", "화장실 앞", "Person"),
    ("손님이 계산 없이 상품을 가방에 넣는 행동이 감지되었습니다.", "과자 진열대", "Person"),
    ("입구에서 취한 것으로 보이는 남성이 비틀거리며 들어왔습니다.", "입구", "Person"),
    ("두 명의 손님이 계산대 앞에서 말다툼 중입니다.", "계산대", "Person"),
    # 차량 관련
    ("주차장에 흰색 SUV 차량이 주차되어 있습니다.", "주차장", "Vehicle"),
    ("검은색 승용차가 편의점 앞 주차구역에 진입했습니다.", "주차장", "Vehicle"),
    ("은색 트럭이 주차장에서 물품을 하역하고 있습니다.", "주차장", "Vehicle"),
    ("빨간색 오토바이가 편의점 앞 인도에 주차되어 있습니다.", "입구", "Vehicle"),
    ("배달 오토바이가 주차장에 잠시 정차했다가 출발했습니다.", "주차장", "Vehicle"),
    ("주차장에 차량 1대가 장시간 주차된 채 방치되어 있습니다.", "주차장", "Vehicle"),
    # 야간 상황
    ("야간에 후드티를 입은 남성이 편의점에 입장했습니다.", "입구", "Person"),
    ("야간 손님이 계산대에서 야식을 구매하고 있습니다.", "계산대", "Person"),
    ("야간에 주차장에서 수상한 인물이 차량 근처를 배회하고 있습니다.", "주차장", "Person"),
    ("야간 배달원이 즉석식품 코너 앞에서 상품을 픽업하고 있습니다.", "즉석식품 코너", "Person"),
    ("야간에 취객으로 보이는 손님이 주류 코너에서 소란을 피우고 있습니다.", "주류 코너", "Person"),
]

# ── 전체 레코드 가져오기 ──────────────────────────────────
resp = supabase.table('cctv_vectors').select('id, metadata').order('id').execute()
records = resp.data
print(f"[INFO] 총 {len(records)}개 레코드 업데이트 시작")

random.seed(42)  # 재현 가능하도록 시드 고정

success = 0
fail = 0
for i, record in enumerate(records):
    scenario = SCENARIOS[i % len(SCENARIOS)]
    content, loc, tag = scenario

    old_meta = record.get('metadata', {})
    new_meta = {
        **old_meta,
        'location': loc,
        'person': tag,
        'confidence': random.randint(82, 99),
    }

    try:
        supabase.table('cctv_vectors') \
            .update({'content': content, 'metadata': new_meta}) \
            .eq('id', record['id']) \
            .execute()
        success += 1
        if i % 20 == 0:
            print(f"  [{i+1}/{len(records)}] ID={record['id']} | {loc} | {content[:40]}...")
    except Exception as e:
        print(f"  [ERROR] ID={record['id']}: {e}")
        fail += 1

print(f"\n[완료] 성공: {success}건 / 실패: {fail}건")
