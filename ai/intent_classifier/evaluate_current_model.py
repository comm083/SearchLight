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
        {"text": "빨간 옷 입은 사람 찾아줘", "expected": "SEARCH"},
        {"text": "어제 밤 주차장 화면 보여줘", "expected": "SEARCH"},
        {"text": "정문 카메라 1번 확인해볼래?", "expected": "SEARCH"},
        {"text": "불난 것 같아 빨리 확인해!", "expected": "EMERGENCY"},
        {"text": "CCTV에 쓰러진 사람이 있어요", "expected": "EMERGENCY"},
        {"text": "후문 카메라 연결이 끊겼어", "expected": "ERROR"},
        {"text": "화면이 너무 어두워서 안보여", "expected": "ERROR"},
        {"text": "검은색 세단 지나갔어?", "expected": "SEARCH"},
        {"text": "오늘 날씨 어때?", "expected": "GENERAL"},
        {"text": "수고 많으십니다", "expected": "GENERAL"}
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
        predicted = result["intent"]
        
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
