from transformers import pipeline

def run_koelectra_test():
    print("1. KoELECTRA 텍스트 분류 모델 로드 중... (최초 다운로드 소요)")
    # 영화 리뷰 데이터로 미리 학습(Fine-tuning)된 KoELECTRA 모델을 불러옵니다.
    # (실제 프로젝트에서는 추후 이 자리에 우리가 직접 '검색 의도'로 학습시킨 모델이 들어가게 됩니다)
    classifier = pipeline(
        "text-classification", 
        model="monologg/koelectra-small-finetuned-nsmc"
    )

    # 2. 테스트용 문장 (사용자 입력)
    user_inputs = [
        "이 시스템 검색 속도가 너무 느려서 답답해",
        "어제 녹화된 CCTV 영상 아주 선명하고 좋네",
        "빨간 옷 입은 사람 찾아줘"
    ]

    print("\n2. 입력된 문장의 문맥/의도 분석 시작...")
    
    # 3. 분류 결과 출력
    print("\n=== KoELECTRA 텍스트 분류 결과 ===")
    for text in user_inputs:
        result = classifier(text)[0]
        label = result['label'] # 모델에 따라 '0'(부정) 또는 '1'(긍정) 등으로 출력됨
        score = result['score'] # AI의 확신도 (0 ~ 1)
        
        # 모델의 출력값을 사람이 이해하기 쉽게 변환
        intent_name = "긍정적 문맥 (Positive)" if label == "1" else "부정적/일반 문맥 (Negative)"
        
        print(f"▶ 입력: '{text}'")
        print(f"  -> 분석 결과: {intent_name} (AI 확신도: {score*100:.1f}%)")

if __name__ == "__main__":
    run_koelectra_test()
