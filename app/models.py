from sqlalchemy import Column, Integer, String, Text, Float
from .database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=False)
    sla_json = Column(Text)
    fairness_score = Column(Float, default=0.0)
    fairness_level = Column(String, default="UNKNOWN")
