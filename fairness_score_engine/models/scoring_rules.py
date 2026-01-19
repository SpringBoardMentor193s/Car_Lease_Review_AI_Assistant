from decimal import Decimal
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, validator


class ScoringMethod(str, Enum):
    Z_SCORE = "z_score"
    CATEGORICAL_MAP = "categorical_map"
    BOOLEAN_RULE = "boolean_rule"


class Direction(str, Enum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"


class Rule(BaseModel):
    """
    Declarative scoring rule for evaluating a single contract field.
    Each rule converts a field value into a 0–100 fairness score.
    """

    field: str
    method: ScoringMethod
    weight: Decimal = Field(..., gt=Decimal("0"), le=Decimal("1"))

    direction: Optional[Direction] = None
    penalty_factor: Optional[Decimal] = Field(None, gt=Decimal("0"))
    categories: Optional[Dict[str, Decimal]] = None

    # ---------- Parsing ----------

    @validator("weight", "penalty_factor", pre=True)
    def parse_decimal(cls, v):
        if v is None:
            return v
        if isinstance(v, (str, float, int)):
            return Decimal(str(v))
        return v

    @validator("categories", pre=True)
    def parse_categories(cls, v):
        if v is None:
            return v
        return {k: Decimal(str(val)) for k, val in v.items()}

    # ---------- Validation ----------

    @validator("categories", always=True)
    def validate_categories_for_method(cls, v, values):
        if values.get("method") == ScoringMethod.CATEGORICAL_MAP:
            if not v:
                raise ValueError("categories must be provided for categorical_map rules")
            for cat, score in v.items():
                if not (Decimal("0") <= score <= Decimal("100")):
                    raise ValueError(f"Category score must be 0–100: {cat}={score}")
        return v

    @validator("penalty_factor", "direction", always=True)
    def validate_zscore_fields(cls, v, values, field):
        if values.get("method") == ScoringMethod.Z_SCORE and v is None:
            raise ValueError(f"{field.name} must be provided for z_score rules")
        return v

    @validator("method")
    def validate_boolean_rule(cls, v, values):
        if v == ScoringMethod.BOOLEAN_RULE:
            if values.get("categories") is not None:
                raise ValueError("boolean_rule must not define categories")
        return v


class ScoringRules(BaseModel):
    """
    Collection of scoring rules indexed by rule name.
    """

    rules: Dict[str, Rule]

    @validator("rules")
    def validate_total_weight(cls, rules):
        total = sum(rule.weight for rule in rules.values())
        if abs(total - Decimal("1")) > Decimal("0.001"):
            raise ValueError(f"Total rule weight must sum to 1.0, got {total}")
        return rules

    def get_rule(self, rule_name: str) -> Rule:
        return self.rules[rule_name]

    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True
        json_encoders = {Decimal: lambda v: str(v)}
