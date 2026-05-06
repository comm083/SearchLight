import os
import shutil
from fastapi import APIRouter, File, UploadFile
from app.services.nlp_service import nlp_service
from app.core.config import settings

router = APIRouter()

@router.post("")
async def speech_to_text(file: UploadFile = File(...)):
    """OpenAI Whisper를 사용한 음성 인식"""
    if not os.path.exists(settings.TEMP_DIR):
        os.makedirs(settings.TEMP_DIR)
        
    temp_file_path = os.path.join(settings.TEMP_DIR, f"stt_{file.filename}")
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text = nlp_service.transcribe_audio(temp_file_path)
        return {"status": "success", "text": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
