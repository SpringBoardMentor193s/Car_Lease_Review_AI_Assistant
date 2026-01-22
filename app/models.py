from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    extracted_text = Column(Text)
