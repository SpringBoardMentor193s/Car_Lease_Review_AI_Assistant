from pydantic import BaseModel, Field
from typing import List, Optional


class SLASummary(BaseModel):
    # Financial Terms
    interest_rate_apr: Optional[float] = Field(
        None, description="Annual Percentage Rate (APR) of the lease"
    )
    lease_term_months: Optional[int] = Field(
        None, description="Lease duration in months"
    )
    monthly_payment: Optional[float] = Field(
        None, description="Monthly lease payment amount"
    )
    down_payment: Optional[float] = Field(
        None, description="Initial down payment amount"
    )
    residual_value: Optional[float] = Field(
        None, description="Residual value of the vehicle at lease end"
    )
    purchase_option_price: Optional[float] = Field(
        None, description="Buyout price if the lessee chooses to purchase"
    )

    # Usage & Mileage
    mileage_allowance_km_per_year: Optional[int] = Field(
        None, description="Allowed mileage per year"
    )
    mileage_overage_fee_per_km: Optional[float] = Field(
        None, description="Charge per extra kilometer beyond allowance"
    )

    # Legal & Responsibility Clauses
    early_termination_clause: Optional[str] = Field(
        None, description="Conditions and penalties for early termination"
    )
    maintenance_responsibility: Optional[str] = Field(
        None, description="Who is responsible for maintenance and repairs"
    )
    warranty_coverage: Optional[str] = Field(
        None, description="Warranty details and coverage period"
    )
    insurance_requirement: Optional[str] = Field(
        None, description="Insurance obligations of the lessee"
    )
    late_fee_penalties: Optional[str] = Field(
        None, description="Late payment penalties or fees"
    )

    # Risk & Fairness Analysis
    red_flags: List[str] = Field(
        default_factory=list,
        description="List of risky or unfair contract clauses"
    )
    fairness_score: Optional[int] = Field(
        None,
        description="Overall contract fairness score (0–100)"
    )
