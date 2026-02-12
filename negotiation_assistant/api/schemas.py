from typing import List
from pydantic import BaseModel, Field

class NegotiationPointSchema(BaseModel):
    topic: str
    current_value: str
    target_value: str
    rationale: str
    leverage: str

class GeneralNegotiationPointSchema(BaseModel):
    topic: str
    advice: str
    strategy: str

class NegotiationAssistantResponse(BaseModel):
    suggested_questions: List[str]
    contract_specific_points: List[NegotiationPointSchema]
    general_points: List[GeneralNegotiationPointSchema]
    chat_template: str

class NegotiationAssistantRequest(BaseModel):
    record_id: int = Field(..., description="Record ID to fetch data from database")

    class Config:
        extra = "forbid"

class EmailGenerationRequestSchema(BaseModel):
    record_id: int = Field(..., description="Record ID to fetch data from database")
    user_tone: str = "professional"

    class Config:
        extra = "forbid"

class EmailTemplateResponseSchema(BaseModel):
    subject: str
    body: str
