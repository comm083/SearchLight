from transformers import pipeline

class IntentClassifierService:
    def __init__(self):
        print("[Service] KoELECTRA 의도 분류기 초기화 중...")
        # 영화 리뷰 데이터를 검색/일반 의도 구분에 임시 활용
        self.classifier = pipeline("text-classification", model="monologg/koelectra-small-finetuned-nsmc")
        print("[Service] KoELECTRA 의도 분류기 로드 완료!")

    def classify(self, text: str):
        result = self.classifier(text)[0]
        label = result['label']
        score = float(result['score'])
        
        # 임시 로직: 1(긍정)을 '검색(SEARCH)'으로, 0(부정)을 '일반(GENERAL)'로 매핑
        intent = "SEARCH" if label == "1" else "GENERAL"
        
        return {
            "intent": intent,
            "confidence": round(score, 4),
            "raw_label": label
        }

# 싱글톤 패턴 (서버 내에서 한 번만 생성되도록)
intent_service = IntentClassifierService()
