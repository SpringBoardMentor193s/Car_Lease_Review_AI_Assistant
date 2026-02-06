"""
API schemas for the Car Lease Review AI Assistant
"""

from typing import Optional, Dict, Any, List
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
    residual_value_amount: Optional[float]
    late_fee_policy: Optional[str]
    maintenance_responsibility: Optional[str]
    maintenance_clause: Optional[str]
    buyout_price: Optional[float]
    warranty_coverage: Optional[str]
    insurance_coverage: Optional[str]
    created_at: str

    class Config:
        orm_mode = True


class VinReportResponse(BaseModel):
    """Response schema for VIN-based vehicle history and risk report."""

    vehicle_identity: Dict[str, Any]
    recall_history: Dict[str, Any]
    theft_and_salvage: Dict[str, Any]
    odometer_analysis: Dict[str, Any]
    paid_reports: Dict[str, Any]
    meta: Dict[str, Any]
    human_summary: str


class OcrHealthResponse(BaseModel):
    """Response schema for OCR health check."""

    tesseract_cmd: str
    tesseract_exists: bool
    pdf2image_available: bool
    poppler_on_path: bool
    poppler_hint: str


class FairnessReportResponse(BaseModel):
    """Response schema for fairness scoring output."""

    overall_score: float
    verdict: str
    subscores: Dict[str, float]
    red_flags: List[str]
    explanations: Dict[str, str]
    engine_version: str


class ScoreResult(BaseModel):
    """Response schema for extraction + scoring."""

    record_id: int
    extracted_data: Dict[str, Any]
    fairness_report: FairnessReportResponse
    status: str = "success"
    message: str = "PDF scored successfully"
