from ai.nlp.sentence_correction import correct_stt_text
import time
import sys
import io

# 한글 출력을 위해 stdout 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def test_correction():
    test_cases = [
        "노랑 오슬 입은 사람이 찍킨게 있어?",
        "씨씨티비 보여조",
        "도둑이 드렀어",
        "사람 찾아",
        "빨간색 오슬 입은 사람 보여"
    ]
    
    print("=== KoBART Sentence Correction Test ===")
    
    for i, text in enumerate(test_cases):
        print(f"\n[Test {i+1}]")
        print(f"Input: {text}")
        
        start_time = time.time()
        corrected = correct_stt_text(text)
        end_time = time.time()
        
        print(f"Output: {corrected}")
        print(f"Time taken: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    # 필요한 패키지 확인 안내
    print("Note: First run may take a while to download the model (approx 500MB).")
    test_correction()
