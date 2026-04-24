from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

# 5가지 의도 카테고리 (train.py와 동일하게 맞춰야 함)
LABEL_MAP = {
    0: "SEARCH",     # 조회
    1: "EMERGENCY",  # 위험
    2: "ERROR",      # 장애
    3: "ACCESS",     # 출입
    4: "GENERAL"     # 일상
}

LABEL_KO = {
    "SEARCH": "조회",
    "EMERGENCY": "위험",
    "ERROR": "장애",
    "ACCESS": "출입",
    "GENERAL": "일상"
}

class IntentClassifierService:
    def __init__(self):
        print("[Service] KoELECTRA 의도 분류기 초기화 중...")

        # 파인튜닝된 모델 경로 (프로젝트 루트 기준 상대 경로)
        finetuned_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'model', 'koelectra_finetuned')
        )

        if os.path.exists(finetuned_path):
            print(f"[Service] -> 파인튜닝된 모델 발견: {finetuned_path}")
            model_path = finetuned_path
        else:
            # 폴백: 파인튜닝 전 임시 모델
            print("[Service] 파인튜닝 모델 없음. 임시 베이스 모델 사용.")
            model_path = "monologg/koelectra-small-finetuned-nsmc"

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()
        print("[Service] KoELECTRA 의도 분류기 로드 완료!")

    def classify(self, text: str):
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            predicted_class = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][predicted_class].item()

        intent_key = LABEL_MAP.get(predicted_class, "GENERAL")

        return {
            "intent": intent_key,
            "intent_ko": LABEL_KO.get(intent_key, "일상"),
            "confidence": round(confidence, 4),
            "raw_label": predicted_class
        }

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
intent_service = IntentClassifierService()
