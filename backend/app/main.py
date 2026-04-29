from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import search, history, alerts

app = FastAPI(title="SearchLight CCTV 통합 검색 API", version="2.4")

# 정적 파일(이미지) 서빙 설정
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS 설정 (프론트엔드의 접근을 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모듈화된 라우터 등록
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
