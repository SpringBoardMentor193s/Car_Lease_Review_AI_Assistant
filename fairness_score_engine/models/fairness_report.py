from decimal import Decimal
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field, validator


class Verdict(str, Enum):
    EXCELLENT = "Excellent"
    FAIR = "Fair"
    RISKY = "Risky"
    UNFAVORABLE = "Unfavorable"


class FairnessReport(BaseModel):
    """
    Final structured output of the fairness evaluation engine.
    """

    overall_score: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100"))
    verdict: Verdict
    subscores: Dict[str, Decimal]

    red_flags: List[str] = Field(default_factory=list)
    explanations: Dict[str, str] = Field(default_factory=dict)
    engine_version: str = Field(default="1.0.0")

    # ---------- Parsing ----------

    @validator("overall_score", pre=True)
    def parse_score(cls, v):
        if isinstance(v, (str, float, int)):
            return Decimal(str(v))
        return v

    @validator("subscores", pre=True)
    def parse_subscores(cls, v):
        return {k: Decimal(str(val)) for k, val in v.items()}

    # ---------- Validation ----------

    @validator("subscores")
    def validate_subscores(cls, v):
        for k, score in v.items():
            if not (Decimal("0") <= score <= Decimal("100")):
                raise ValueError(f"Subscore '{k}' must be 0–100, got {score}")
        return v

    # ---------- Helpers ----------

    def is_acceptable(self, threshold: Decimal = Decimal("60")) -> bool:
        return self.overall_score >= threshold

    def get_worst_subscore(self) -> tuple[str, Decimal]:
        return min(self.subscores.items(), key=lambda x: x[1])

    def get_best_subscore(self) -> tuple[str, Decimal]:
        return max(self.subscores.items(), key=lambda x: x[1])

    def add_red_flag(self, flag: str):
        if flag and flag not in self.red_flags:
            self.red_flags.append(flag)

    def add_explanation(self, field: str, explanation: str):
        if field and explanation:
            self.explanations[field] = explanation

    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True
        json_encoders = {Decimal: lambda v: str(v)}
