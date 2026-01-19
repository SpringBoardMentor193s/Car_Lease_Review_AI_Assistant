"""
Canonical domain models for the Fairness Engine.

These models define the strict data contracts between:
- LLM extraction layer
- Fairness scoring engine
- API layer
- Frontend consumers

All schemas are auto-generated from these models.
"""

from .contract_facts import ContractFacts, MaintenanceResponsibility
from .scoring_rules import ScoringRules, Rule, ScoringMethod, Direction
from .fairness_report import FairnessReport, Verdict

__all__ = [
    "ContractFacts",
    "MaintenanceResponsibility",
    "ScoringRules",
    "Rule",
    "ScoringMethod",
    "Direction",
    "FairnessReport",
    "Verdict",
]
