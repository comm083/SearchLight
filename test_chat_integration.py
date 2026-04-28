import chat
from unittest.mock import patch

def test_chatbot():
    # 여러 테스트 케이스 시뮬레이션
    test_inputs = [
        "노랑 오슬 입은 사람이 찍킨게 있어?",
        "씨씨티비 보여조",
        "도둑이 드렀어",
        "q"
    ]
    
    print("=== Chatbot Integration Test Start ===")
    with patch('builtins.input', side_effect=test_inputs):
        chat.main()
    print("\n=== Chatbot Integration Test End ===")

if __name__ == "__main__":
    test_chatbot()
