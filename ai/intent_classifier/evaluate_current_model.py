import sys
import os

# 백엔드 모듈을 임포트하기 위해 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.services.intent_classifier import intent_service

def evaluate_current_model():
    print("--- 현재(Pre-trained) 모델 성능 평가 시작 ---")
    
    # 1. 평가용 테스트 데이터 (정답 라벨 포함)
    # 실제 환경에서 자주 쓰일 법한 발화 10개를 선정
    test_data = [
        {"text": "빨간 옷 입은 사람 총 몇 명이야?", "expected": "COUNTING"},
        {"text": "어제 오후에 무슨 일 있었어?", "expected": "SUMMARIZATION"},
        {"text": "지금 주차장에 차 있어?", "expected": "LOCALIZATION"},
        {"text": "수상한 사람 없었어?", "expected": "BEHAVIORAL"},
        {"text": "왜 30분 전에 알람이 울렸어?", "expected": "CAUSAL"},
        {"text": "오늘 오전 상황 요약해줘", "expected": "SUMMARIZATION"},
        {"text": "현재 로비에 인원 몇 명인지 세어봐", "expected": "COUNTING"},
        {"text": "담 넘으려는 사람 감지됐어?", "expected": "BEHAVIORAL"},
        {"text": "그 사고 어떻게 발생한 거야?", "expected": "CAUSAL"},
        {"text": "안녕 반가워", "expected": "CHITCHAT"}
    ]
    
    correct_count = 0
    total_count = len(test_data)
    
    print(f"{'입력 텍스트':<30} | {'정답(Expected)':<15} | {'예측(Predicted)':<15} | {'정답 여부'}")
    print("-" * 80)
    
    for item in test_data:
        text = item["text"]
        expected = item["expected"]
        
        # 현재 모델로 예측
        result = intent_service.classify(text)
        predicted = result.intent
        
        is_correct = (expected == predicted)
        if is_correct:
            correct_count += 1
            
        mark = "OK" if is_correct else "FAIL"
        
        # 출력 포맷팅
        print(f"{text[:28]:<30} | {expected:<15} | {predicted:<15} | {mark}")

    # 2. 성능 지표(숫자) 계산
    accuracy = (correct_count / total_count) * 100
    
    print("-" * 80)
    print("[성능 평가 결과 (수치화)]")
    print(f"총 테스트 개수 : {total_count}개")
    print(f"정답 개수      : {correct_count}개")
    print(f"오답 개수      : {total_count - correct_count}개")
    print(f"현재 모델 정확도(Accuracy): {accuracy:.1f}%")
    
    if accuracy < 50:
        print("\n결론: 현재 모델의 정확도가 낮습니다. 추가 학습이 필요할 수 있습니다.")
    else:
        print("\n결론: 모델 성능이 향상되었습니다!")

if __name__ == "__main__":
    evaluate_current_model()
