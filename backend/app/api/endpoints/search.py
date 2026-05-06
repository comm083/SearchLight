import os
import shutil
from fastapi import APIRouter, File, UploadFile, Depends
from app.schemas import SearchRequest, SearchResponse
from app.services.search_manager import search_manager
from app.services.image_search_service import image_search_service
from app.core.config import settings

router = APIRouter()

@router.post("", response_model=SearchResponse)
async def process_user_query(request: SearchRequest):
    return await search_manager.process_query(
        query=request.query,
        session_id=request.session_id,
        top_k=request.top_k
    )

@router.post("/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = 3):
    if not os.path.exists(settings.TEMP_DIR):
        os.makedirs(settings.TEMP_DIR)
        
    temp_file_path = os.path.join(settings.TEMP_DIR, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        results = image_search_service.search(temp_file_path, top_k=top_k)
        return {
            "status": "success",
            "message": f"검색 결과 {len(results)}건 발견",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
