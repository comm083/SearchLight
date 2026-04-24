from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base
import datetime

class YoloEvent(Base):
    __tablename__ = "yolo_events"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    label = Column(String, index=True)  # person, car, etc.
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
<<<<<<< HEAD
    description = Column(String) # 상세 묘사 (RAG 연동용)
=======
    description = Column(String)  # 상세 묘사 (RAG 연동용)
>>>>>>> 4ff8556a21ba92b5e409aa53ab0ab97ae585061e

class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String)
    intent = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
