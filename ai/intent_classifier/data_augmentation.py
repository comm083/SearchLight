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
    이 시스템의 주요 사용처는 '학원'과 '대형 주차장'입니다.
    사용자들의 의도 카테고리 중 '{category_name}' 에 해당하는 매우 자연스럽고 다양한 한국어 질문(발화)을 {num_samples}개 생성해주세요.
    실제 학원 강사나 원장, 혹은 주차장 관리인이 CCTV 시스템에 질문할 법한 상황(예: 학생 다툼, 학부모 컴플레인, 기물 파손, 차량 긁힘, 이중주차, 불법주차 등)을 반영해주세요.
    응답은 번호 없이 각 줄에 하나씩 질문만 작성해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates training data in Korean."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        import re
        cleaned_texts = []
        for line in content.split('\n'):
            if line.strip():
                cleaned = re.sub(r'^\d+\.\s*', '', line.strip().strip('-').strip('.').strip())
                cleaned = cleaned.strip('"\'')
                cleaned_texts.append(cleaned)
        
        return [{"text": text, "label": intent_id} for text in cleaned_texts[:num_samples]]
        
    except Exception as e:
        print(f"Error generating data for intent {intent_id}: {e}")
        return []

def build_dataset():
    """
    기존 데이터셋을 로드하고, GPT를 통해 부족한 데이터를 대량 증강하여 
    클래스당 최소 150건 이상의 풍부한 데이터셋을 구축합니다.
    """
    csv_path = "ai/intent_classifier/intent_dataset.csv"
    if os.path.exists(csv_path):
        print(f"[Info] 기존 데이터셋 로드 중: {csv_path}")
        existing_df = pd.read_csv(csv_path, encoding="utf-8-sig")
    else:
        existing_df = pd.DataFrame(columns=["text", "label"])

    augmented_data = []
    for i in range(5):
        print(f"Generating 200 new samples for: {INTENT_CATEGORIES[i]}...")
        # 클래스별로 200개씩 추가 생성
        new_data = generate_augmented_data(intent_id=i, num_samples=200)
        augmented_data.extend(new_data)

    # 데이터 결합
    new_df = pd.DataFrame(augmented_data)
    total_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # 중복 문장 제거
    total_df = total_df.drop_duplicates(subset=['text']).reset_index(drop=True)
    
    # 셔플
    total_df = total_df.sample(frac=1).reset_index(drop=True)
    
    # CSV 저장
    total_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Dataset successfully expanded! Total records: {len(total_df)}")

if __name__ == "__main__":
    build_dataset()
