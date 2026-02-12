from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class NegotiationRequest(BaseModel):
    contract_facts: Dict = Field(..., description="Extracted contract facts")
    fairness_report: Optional[Dict] = Field(None, description="Fairness report results")
    user_objectives: Optional[List[str]] = Field(None, description="User's specific negotiation goals")
    market_data: Optional[Dict] = Field(None, description="Relevant market benchmarks")

class NegotiationPoint(BaseModel):
    topic: str = Field(..., description="The contract term to negotiate (e.g., APR, Mileage)")
    current_value: str = Field(..., description="The value currently in the contract")
    target_value: str = Field(..., description="The suggested target value for negotiation")
    rationale: str = Field(..., description="Why this point should be negotiated")
    leverage: str = Field(..., description="Points of leverage or arguments to use")

class GeneralNegotiationPoint(BaseModel):
    topic: str = Field(..., description="General area of negotiation (e.g., Documentation Fees)")
    advice: str = Field(..., description="General advice for this topic")
    strategy: str = Field(..., description="How to approach this with the dealer")

class NegotiationResponse(BaseModel):
    suggested_questions: List[str] = Field(..., description="Questions to ask the dealer")
    contract_specific_points: List[NegotiationPoint] = Field(..., description="Points specifically based on the contract facts")
    general_points: List[GeneralNegotiationPoint] = Field(..., description="General market-based negotiation advice")
    chat_template: str = Field(..., description="A draft chat message to the dealer")

class EmailGenerationRequest(BaseModel):
    contract_facts: Dict = Field(..., description="Extracted contract facts")
    negotiation_points: List[NegotiationPoint] = Field(..., description="Selected negotiation points to include in the email")
    user_tone: str = Field("professional", description="The tone of the email (e.g., professional, firm, friendly)")

class EmailTemplateResponse(BaseModel):
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
