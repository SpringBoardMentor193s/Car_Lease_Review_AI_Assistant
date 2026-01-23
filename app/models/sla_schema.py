from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SLASummary(BaseModel):
    # Financial Terms
    interest_rate_apr: Optional[float] = None
    lease_term_months: Optional[int] = None
    monthly_payment: Optional[float] = None
    down_payment: Optional[float] = None
    residual_value: Optional[float] = None
    purchase_option_price: Optional[float] = None

    # Usage & Mileage
    mileage_allowance_km_per_year: Optional[int] = None
    mileage_overage_fee_per_km: Optional[float] = None

    # Legal & Responsibility Clauses (DICT ONLY)
    early_termination_clause: Optional[Dict[str, Any]] = None
    maintenance_responsibility: Optional[str] = None
    warranty_coverage: Optional[Dict[str, Any]] = None
    insurance_requirement: Optional[str] = None
    late_fee_penalties: Optional[Dict[str, Any]] = None

    # Risk & Fairness
    red_flags: List[str] = []
    fairness_score: Optional[float] = None
