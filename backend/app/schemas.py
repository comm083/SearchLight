from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchRequest(BaseModel):
    query: str = Field(..., description="사용자 검색 질의")
    top_k: int = Field(2, description="검색 결과 개수")
    session_id: str = Field("default", description="사용자 세션 ID")
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class IntentInfo(BaseModel):
    intent: str
    confidence: float
    method: str

class TimeInfo(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    raw: str = "전체"

class SearchResponse(BaseModel):
    status: str = "success"
    message: str
    intent_info: IntentInfo
    time_info: TimeInfo
    context_used: bool = False
    response_mode: str = "summary"
    results: List[Dict[str, Any]] = []
    ai_report: Optional[str] = None
    answer: Optional[str] = None

class HistoryResponse(BaseModel):
    status: str = "success"
    history: List[Dict[str, Any]]

