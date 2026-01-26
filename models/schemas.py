from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class LeaseSLA(BaseModel):
    apr: str
    lease_term: str
    monthly_payment: str
    down_payment: str
    residual_value: str
    mileage_limit: str
    early_termination_fee: str
    red_flags: List[str]
    fairness_score: int

class VehicleDetails(BaseModel):
    vin: str
    specifications: Dict[str, Any]
    recalls: List[Dict[str, Any]]
    recall_count: int

class AnalysisRequest(BaseModel):
    contract_text: str
    vehicle_details: Optional[VehicleDetails]

class AnalysisResponse(BaseModel):
    lease_terms: LeaseSLA
    recommended_changes: List[str]
    market_comparison: Dict[str, Any]
    risk_assessment: Dict[str, Any]