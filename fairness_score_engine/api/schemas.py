"""
API schemas for the Car Lease Review AI Assistant
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ExtractionResult(BaseModel):
    """Response schema for extraction results"""
    record_id: int
    extracted_data: Dict[str, Any]
    status: str = "success"
    message: str = "PDF processed successfully"

class ExtractionError(BaseModel):
    """Error response schema"""
    status: str = "error"
    message: str
    details: Optional[Dict[str, Any]] = None

class ContractFactsResponse(BaseModel):
    """Response schema for retrieving stored contract facts"""
    id: int
    apr: Optional[float]
    monthly_payment: Optional[float]
    lease_term_months: Optional[int]
    down_payment: Optional[float]
    mileage_limit_per_year: Optional[int]
    overage_fee_per_mile: Optional[float]
    early_termination_policy: Optional[str]
    residual_value_percent: Optional[float]
    late_fee_policy: Optional[str]
    maintenance_responsibility: Optional[str]
    buyout_price: Optional[float]
    warranty_coverage: Optional[str]
    insurance_coverage: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
