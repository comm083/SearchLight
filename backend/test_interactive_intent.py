import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.intent_classifier import intent_service

def interactive_test():
    print("--- 실시간 의도 분류 테스트 (종료하려면 'exit' 입력) ---")
    while True:
        user_input = input("\n분류할 문장을 입력하세요: ")
        if user_input.lower() == 'exit':
            break
        
        # 실제 AI 모델 서비스를 호출하여 분류
        result = intent_service.classify(user_input)
        
        print(f"입력: {user_input}")
        print(f"판별된 의도: {result['intent']}")
        print(f"확신도(Confidence): {result['confidence'] * 100:.2f}%")
        print(f"원래 모델 결과: {result['raw_label']}")

if __name__ == "__main__":
    interactive_test()
