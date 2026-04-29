import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class Config:
    # Supabase Settings
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Vector DB Settings
    VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "faiss_index.bin")
    METADATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "metadata.json")

    # Storage Settings
    STORAGE_BUCKET = "cctv-clips"

config = Config()
