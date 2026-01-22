from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from .database import Base

# --- SQLAlchemy Models ---

class ContractBase(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    extracted_text = Column(Text, nullable=True)
    
    # Analysis Results (Stored as JSON)
    clauses = Column(JSON, nullable=True)
    fairness_score = Column(Float, nullable=True)
    fairness_explanation = Column(Text, nullable=True)
    market_price_min = Column(Float, nullable=True)
    market_price_max = Column(Float, nullable=True)
    vin_info = Column(JSON, nullable=True)

class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String) # user/assistant
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Pydantic Schemas ---

class ContractCreate(BaseModel):
    filename: str

class ContractResponse(ActionBase := BaseModel):
    id: int
    filename: str
    upload_date: datetime
    extracted_text: Optional[str] = None
    clauses: Optional[Dict[str, Any]] = None
    fairness_score: Optional[float] = None
    fairness_explanation: Optional[str] = None
    market_price_min: Optional[float] = None
    market_price_max: Optional[float] = None
    vin_info: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None # Or specific context ID

class ChatResponse(BaseModel):
    response: str
