"""
Car lease/loan contract representation for fairness evaluation.
Production-grade with financial precision and security.
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from datetime import date

from pydantic import BaseModel, Field, validator, root_validator


class MaintenanceResponsibility(str, Enum):
    LESSEE = "lessee"
    LESSOR = "lessor"
    SHARED = "shared"


class ContractFacts(BaseModel):
    """
    Canonical structured representation of a car lease or loan contract.
    Single source of truth for fairness evaluation.
    """

    # Required fields
    apr: Decimal = Field(..., ge=Decimal("0"), le=Decimal("40"))
    monthly_payment: Decimal = Field(..., ge=Decimal("0"))
    lease_term_months: int = Field(..., ge=1, le=120)

    # Optional fields
    down_payment: Optional[Decimal] = Field(None, ge=Decimal("0"))
    mileage_limit_per_year: Optional[int] = Field(None, ge=0)
    overage_fee_per_mile: Optional[Decimal] = Field(None, ge=Decimal("0"))
    early_termination_policy: Optional[str] = None
    residual_value_percent: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("100"))
    late_fee_policy: Optional[str] = None
    maintenance_responsibility: Optional[MaintenanceResponsibility] = None

    # ---------- Parsing ----------

    @validator("apr", "monthly_payment", "down_payment", "overage_fee_per_mile", "residual_value_percent", pre=True)
    def parse_decimals(cls, v):
        if v is None:
            return v
        if isinstance(v, (str, float, int)):
            return Decimal(str(v))
        return v

    # ---------- Validation ----------

    @validator("apr")
    def validate_apr(cls, v: Decimal) -> Decimal:
        if v > Decimal("25"):
            raise ValueError(f"APR of {v}% exceeds reasonable threshold of 25%")
        return v.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    @validator("monthly_payment", "down_payment", "overage_fee_per_mile")
    def round_money(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return v

    @validator("residual_value_percent")
    def round_residual(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            return v.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return v

    @root_validator
    def validate_down_payment(cls, values):
        monthly = values.get("monthly_payment")
        down = values.get("down_payment")
        if monthly and down and down > monthly * 24:
            raise ValueError("Down payment exceeds 24 months of payments")
        return values

    # ---------- Business Logic ----------

    def calculate_total_cost(self) -> Decimal:
        total = self.monthly_payment * self.lease_term_months
        if self.down_payment:
            total += self.down_payment
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def is_high_risk(self) -> bool:
        if self.apr > Decimal("18"):
            return True
        if self.lease_term_months > 84:
            return True
        if self.residual_value_percent and self.residual_value_percent < Decimal("40"):
            return True
        return False

    class Config:
        extra = "forbid"
        anystr_strip_whitespace = True
        arbitrary_types_allowed = True
        json_encoders = {
            Decimal: lambda v: str(v),
            date: lambda v: v.isoformat(),
        }
