"""
시간 파싱 모듈 (Time Parser)
"어제 오후 3시", "3일 전 오전 10시" 같은 자연어 시간 표현을 
datetime 객체로 변환합니다.
"""
from datetime import datetime, timedelta
import re


def parse_time_expression(text: str) -> dict:
    """
    자연어 텍스트에서 시간 표현을 추출하여 시작~끝 시간 범위를 반환합니다.

    반환 형식:
    {
        "start_time": "2026-04-23 15:00:00",
        "end_time":   "2026-04-23 15:59:59",
        "raw":        "어제 오후 3시"
    }
    변환 실패 시 None을 반환합니다.
    """
    now = datetime.now()
    result = {"start_time": None, "end_time": None, "raw": None}

    # ----- 1. 기준 날짜 파싱 -----
    base_date = now.date()

    if "그저께" in text or "그제" in text:
        base_date = (now - timedelta(days=2)).date()
    elif "어제" in text:
        base_date = (now - timedelta(days=1)).date()
    elif "오늘" in text or "지금" in text:
        base_date = now.date()
    else:
        # N일 전 패턴: "3일 전", "2일전"
        day_ago_match = re.search(r"(\d+)\s*일\s*전", text)
        if day_ago_match:
            days = int(day_ago_match.group(1))
            base_date = (now - timedelta(days=days)).date()

        # N시간 전 패턴: "2시간 전"
        hour_ago_match = re.search(r"(\d+)\s*시간\s*전", text)
        if hour_ago_match:
            hours = int(hour_ago_match.group(1))
            start_dt = now - timedelta(hours=hours)
            end_dt = now
            result["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            result["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            result["raw"] = hour_ago_match.group(0)
            return result

    # ----- 2. 시각 파싱 -----
    hour = None
    minute = 0

    # 오전/오후 + 시 + 분(선택) 패턴
    time_match = re.search(
        r"(오전|오후|낮|밤|새벽)?\s*(\d{1,2})\s*시\s*(\d{1,2})?\s*분?", text
    )
    if time_match:
        period = time_match.group(1)  # 오전/오후/낮/밤/새벽 (없으면 None)
        hour = int(time_match.group(2))
        minute = int(time_match.group(3)) if time_match.group(3) else 0

        if period in ("오후", "밤") and hour < 12:
            hour += 12
        elif period in ("새벽",) and hour == 12:
            hour = 0
        elif period is None:
            # 오전/오후 힌트 없이 시각만 있을 때: 0~6시는 새벽, 나머지는 그대로 사용
            pass

        result["raw"] = time_match.group(0).strip()

    # ----- 3. 결과 조합 -----
    if hour is not None:
        start_dt = datetime(
            base_date.year, base_date.month, base_date.day, hour, minute, 0
        )
        # 분 단위 범위: 지정 분 ~ 해당 시의 59분 59초
        end_dt = start_dt.replace(second=59, microsecond=0)
        if minute == 0:
            # "3시"만 입력 → 3:00 ~ 3:59
            end_dt = start_dt.replace(minute=59, second=59)
        result["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        result["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # 시각 없이 날짜만 → 하루 전체
        start_dt = datetime(base_date.year, base_date.month, base_date.day, 0, 0, 0)
        end_dt = datetime(base_date.year, base_date.month, base_date.day, 23, 59, 59)
        result["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        result["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        result["raw"] = "날짜 전체"

    return result


# ===== 간단한 테스트 =====
if __name__ == "__main__":
    test_cases = [
        "어제 오후 3시 주차장 화면 보여줘",
        "그저께 오전 10시 30분 정문 확인",
        "3일 전 CCTV 기록 찾아줘",
        "오늘 밤 11시 이후 기록 있어?",
        "2시간 전에 사람 지나갔어?",
        "새벽 2시 이상한 사람 있었어",
        "오늘 전체 기록 보여줘",
    ]

    for text in test_cases:
        result = parse_time_expression(text)
        print(f"입력: {text}")
        print(f"  → start: {result['start_time']} | end: {result['end_time']}")
        print()
