from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
from .classifier import IntentClassifier

app = FastAPI(title="SearchLight Intent Classifier API")

# 전역 모델 인스턴스 (앱 시작 시 로드)
# 실제 환경에서는 학습된 모델 경로를 지정해야 합니다.
# 예: classifier.load_model("./saved_model")
classifier = IntentClassifier()

class QueryRequest(BaseModel):
    text: str

class IntentResponse(BaseModel):
    text: str
    intent_id: int
    intent_label: str
    confidence: float
    probabilities: Dict[str, float]

@app.post("/predict", response_model=IntentResponse)
async def predict_intent(request: QueryRequest):
    """
    사용자 질의의 의도를 5가지 카테고리로 분류하여 반환합니다.
    (시간, 사람 수, 행동, 정보 요약, 오류 감지)
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    try:
        # 인퍼런스 수행
        result = classifier.predict(request.text)
        return IntentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """서버 상태 확인용"""
    return {"status": "ok"}

