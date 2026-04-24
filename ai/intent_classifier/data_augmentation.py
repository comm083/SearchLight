from openai import OpenAI
import pandas as pd
import json
import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 5가지 분류 카테고리 정의
INTENT_CATEGORIES = {
    0: "조회 (정보 확인)",
    1: "위험 (이상 상황 / 긴급)",
    2: "장애 (시스템 문제)",
    3: "출입 (사람/차량 이동)",
    4: "일상 (일반 대화 / 비업무)"
}

def generate_augmented_data(intent_id: int, num_samples: int = 10):
    """
    GPT API를 사용하여 특정 의도에 대한 발화(Question) 데이터를 증강합니다.
    """
    category_name = INTENT_CATEGORIES[intent_id]
    
    prompt = f"""
    당신은 CCTV 및 웹캠 보안 시스템 'SearchLight'의 챗봇 AI를 학습시키기 위한 데이터 생성기입니다.
    사용자들의 의도 카테고리 중 '{category_name}' 에 해당하는 매우 자연스럽고 다양한 한국어 질문(발화)을 {num_samples}개 생성해주세요.
    실제 보안 담당자나 일반 사용자가 CCTV 시스템에 질문할 법한 형태여야 합니다.
    응답은 다른 설명 없이 각 줄에 하나씩 질문만 작성해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates training data in Korean."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        # 개행 문자로 분리하고 빈 줄 제거
        generated_texts = [line.strip().strip('-').strip('.').strip() for line in content.split('\n') if line.strip()]
        
        return [{"text": text, "label": intent_id} for text in generated_texts[:num_samples]]
        
    except Exception as e:
        print(f"Error generating data for intent {intent_id}: {e}")
        return []

def build_dataset():
    """
    직접 구축한 데이터(30%)와 GPT로 증강한 데이터(70%)를 결합하여 
    총 300건의 데이터셋을 구축합니다. (각 클래스당 60건씩)
    """
    # 1. 수동으로 작성된 초기 시드 데이터 예시 (직접 30% - 총 90건 중 일부)
    manual_data = [
        {"text": "어제 오후 3시 주차장 화면 보여줘", "label": 0},
        {"text": "정문 카메라 1번 확인해볼래?", "label": 0},
        {"text": "불난 것 같아 빨리 확인해!", "label": 1},
        {"text": "CCTV에 쓰러진 사람이 있어요", "label": 1},
        {"text": "후문 카메라 연결이 끊겼어", "label": 2},
        {"text": "화면이 너무 어두워서 안보여", "label": 2},
        {"text": "검은색 세단 지나갔어?", "label": 3},
        {"text": "외부인 출입 기록 좀 찾아줘", "label": 3},
        {"text": "오늘 날씨 어때?", "label": 4},
        {"text": "수고 많으십니다", "label": 4},
    ]
    
    # 현실적으로는 수동 데이터가 90건 필요함
    # 여기서는 데모를 위해 바로 GPT 증강으로 채웁니다 (70% = 210건)
    
    augmented_data = []
    # 각 클래스별로 필요한 증강 개수 (예: 클래스당 42개씩 생성해서 210건)
    # 실제로는 manual_data 개수 파악 후 부족분만큼 생성
    for i in range(5):
        print(f"Generating augmented data for: {INTENT_CATEGORIES[i]}...")
        # API 호출 비용 및 시간 절약을 위해 처음에는 클래스당 20개씩 생성 (총 100개)
        new_data = generate_augmented_data(intent_id=i, num_samples=40)
        augmented_data.extend(new_data)

    # 데이터 결합
    total_dataset = manual_data + augmented_data
    
    # DataFrame 변환 및 저장
    df = pd.DataFrame(total_dataset)
    # 셔플
    df = df.sample(frac=1).reset_index(drop=True)
    
    # CSV 저장
    df.to_csv("intent_dataset.csv", index=False, encoding="utf-8-sig")
    print(f"Dataset successfully saved with {len(df)} records.")

if __name__ == "__main__":
    build_dataset()
