"""
cctv_vectors 테이블의 metadata.timestamp를
오늘(2026-05-06) 기준으로 1일 2개씩 과거 날짜에 균등 분배하는 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.services.database import db_service

supabase = db_service.supabase

# 1. 전체 레코드 ID 목록 가져오기 (ID 오름차순)
resp = supabase.table('cctv_vectors').select('id, metadata').order('id').execute()
records = resp.data
print(f"[INFO] 총 {len(records)}개 레코드 발견")

# 2. 날짜 분배 계획 수립
# 오늘부터 과거 방향으로, 하루에 2개씩, 시각은 09:30 / 15:45로 고정
TODAY = datetime(2026, 5, 6)
TIMES_PER_DAY = [("09", "30"), ("15", "45")]

# 날짜×시간 슬롯 생성 (오늘 → 과거 방향, 레코드 수만큼)
slots = []
day_offset = 0
while len(slots) < len(records):
    date = TODAY - timedelta(days=day_offset)
    for hour, minute in TIMES_PER_DAY:
        ts = date.strftime(f"%Y-%m-%d {hour}:{minute}:00")
        slots.append(ts)
        if len(slots) >= len(records):
            break
    day_offset += 1

print(f"[INFO] 슬롯 생성 완료: {slots[0]} ~ {slots[-1]}")

# 3. Supabase metadata.timestamp 업데이트
success = 0
fail = 0
for i, record in enumerate(records):
    new_ts = slots[i]
    old_meta = record.get('metadata', {})
    new_meta = {**old_meta, 'timestamp': new_ts}

    try:
        supabase.table('cctv_vectors') \
            .update({'metadata': new_meta}) \
            .eq('id', record['id']) \
            .execute()
        success += 1
        if i % 20 == 0:
            print(f"  [{i+1}/{len(records)}] ID={record['id']} → {new_ts}")
    except Exception as e:
        print(f"  [ERROR] ID={record['id']}: {e}")
        fail += 1

print(f"\n[완료] 성공: {success}건 / 실패: {fail}건")
print(f"날짜 범위: {slots[-1][:10]} ~ {slots[0][:10]}")
