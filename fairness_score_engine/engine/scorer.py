"""
Rule-driven fairness scoring engine.
"""

import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

from models.contract_facts import ContractFacts
from models.fairness_report import FairnessReport, Verdict
from models.scoring_rules import ScoringRules, Rule, ScoringMethod, Direction

logger = logging.getLogger(__name__)


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        try:
            return Decimal(str(value))
        except Exception:
            return None
    return None


def _clamp(score: Decimal, lo: Decimal = Decimal("0"), hi: Decimal = Decimal("100")) -> Decimal:
    if score < lo:
        return lo
    if score > hi:
        return hi
    return score


class FairnessScorer:
    """
    Evaluate ContractFacts using declarative ScoringRules and market benchmarks.
    """

    def __init__(self, rules: ScoringRules, benchmarks: Dict[str, Dict[str, Any]]):
        self.rules = rules
        self.benchmarks = benchmarks or {}

    def score(self, facts: ContractFacts) -> FairnessReport:
        subscores: Dict[str, Decimal] = {}
        explanations: Dict[str, str] = {}
        red_flags = []

        for rule_name, rule in self.rules.rules.items():
            value = getattr(facts, rule.field, None)
            score, explanation, flag = self._score_rule(rule, value)
            subscores[rule_name] = score
            if explanation:
                explanations[rule_name] = explanation
            if flag:
                red_flags.append(flag)

        overall_score = self._weighted_average(subscores)
        verdict = self._verdict(overall_score)

        # Contract-level red flags
        if facts.is_high_risk():
            red_flags.append("Contract flagged as high risk based on core terms")

        # Missing key terms red flag
        missing_terms = []
        if facts.down_payment is None:
            missing_terms.append("down payment")
        if facts.residual_value_percent is None and facts.residual_value_amount is None:
            missing_terms.append("residual value")
        if facts.mileage_limit_per_year is None:
            missing_terms.append("mileage allowance")
        if facts.overage_fee_per_mile is None:
            missing_terms.append("overage fee")
        if facts.buyout_price is None:
            missing_terms.append("purchase option price")
        if missing_terms:
            red_flags.append(
                "Missing key terms: " + ", ".join(missing_terms)
            )

        clause_flags, clause_explanations = self._analyze_clause_red_flags(facts)
        red_flags.extend(clause_flags)
        explanations.update(clause_explanations)

        return FairnessReport(
            overall_score=overall_score,
            verdict=verdict,
            subscores=subscores,
            red_flags=red_flags,
            explanations=explanations,
        )

    def _weighted_average(self, subscores: Dict[str, Decimal]) -> Decimal:
        total = Decimal("0")
        for rule_name, rule in self.rules.rules.items():
            score = subscores.get(rule_name, Decimal("50"))
            total += score * rule.weight
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _verdict(self, score: Decimal) -> Verdict:
        if score >= Decimal("80"):
            return Verdict.EXCELLENT
        if score >= Decimal("65"):
            return Verdict.FAIR
        if score >= Decimal("50"):
            return Verdict.RISKY
        return Verdict.UNFAVORABLE

    def _score_rule(self, rule: Rule, value: Any) -> tuple[Decimal, str, Optional[str]]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return Decimal("50"), f"{rule.field} not found; default score applied", None

        if rule.method == ScoringMethod.Z_SCORE:
            return self._score_z(rule, value)
        if rule.method == ScoringMethod.CATEGORICAL_MAP:
            return self._score_categorical(rule, value)
        if rule.method == ScoringMethod.BOOLEAN_RULE:
            return self._score_boolean(rule, value)

        return Decimal("50"), f"Unknown method for {rule.field}; default score applied", None

    def _score_z(self, rule: Rule, value: Any) -> tuple[Decimal, str, Optional[str]]:
        val = _to_decimal(value)
        if val is None:
            return Decimal("50"), f"{rule.field} value invalid; default score applied", None

        benchmark = self.benchmarks.get(rule.field, {})
        mean = _to_decimal(benchmark.get("mean")) or Decimal("0")
        std = _to_decimal(benchmark.get("std")) or Decimal("1")
        min_val = _to_decimal(benchmark.get("min"))
        max_val = _to_decimal(benchmark.get("max"))

        z = (val - mean) / std if std != 0 else Decimal("0")
        if rule.direction == Direction.LOWER_BETTER:
            z = -z

        penalty = rule.penalty_factor or Decimal("10")
        raw_score = Decimal("50") + (z * penalty)
        score = _clamp(raw_score)

        flag = None
        if min_val is not None and val < min_val:
            flag = f"{rule.field} below market minimum"
        if max_val is not None and val > max_val:
            flag = f"{rule.field} above market maximum"
        if score < Decimal("40"):
            flag = flag or f"{rule.field} scored poorly"

        explanation = (
            f"{rule.field}={val} vs market mean {mean} (std {std}); "
            f"direction {rule.direction.value if rule.direction else 'neutral'}"
        )
        return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), explanation, flag

    def _analyze_clause_red_flags(self, facts: ContractFacts) -> tuple[list[str], Dict[str, str]]:
        flags: list[str] = []
        explanations: Dict[str, str] = {}

        def norm(text: Optional[str]) -> str:
            return re.sub(r"\s+", " ", (text or "")).strip().lower()

        def add(flag: str, field: str, detail: str):
            if flag not in flags:
                flags.append(flag)
            explanations[field] = detail

        early = norm(facts.early_termination_policy)
        if early:
            if re.search(r"per\s*(?:mile|km)|over\s+\d{4,6}\s*(?:miles|km)", early):
                add(
                    "Early termination clause may be mis-extracted (looks like mileage overage)",
                    "early_termination_policy",
                    "Clause contains mileage overage language; verify extraction.",
                )
            if re.search(r"all remaining payments|accelerat|entire balance|liquidated damages", early):
                add(
                    "Early termination requires payment of all remaining amounts",
                    "early_termination_policy",
                    "Clause indicates accelerated or full remaining payment obligation.",
                )
            if re.search(r"non[- ]?refundable|no refund|forfeit", early):
                add(
                    "Early termination includes non-refundable or forfeiture language",
                    "early_termination_policy",
                    "Clause suggests loss of prepaid amounts or deposits.",
                )
            if re.search(r"sole discretion|any reason|without cause", early):
                add(
                    "Early termination rights appear one-sided",
                    "early_termination_policy",
                    "Termination appears to favor one party without cause.",
                )

        late_fee = norm(facts.late_fee_policy)
        if late_fee:
            if re.search(r"per day|daily|each day", late_fee):
                add(
                    "Late fee is assessed daily",
                    "late_fee_policy",
                    "Daily late fees can accumulate quickly.",
                )
            amount = self._extract_money_amount(late_fee)
            if amount is not None and amount > Decimal("35"):
                add(
                    "Late fee amount appears high",
                    "late_fee_policy",
                    f"Late fee mentions about ${amount}.",
                )
            percent = self._extract_percent(late_fee)
            if percent is not None and percent > Decimal("3"):
                add(
                    "Late fee percentage appears high",
                    "late_fee_policy",
                    f"Late fee mentions about {percent}%.",
                )

        warranty = norm(facts.warranty_coverage)
        if warranty:
            if re.search(r"as is|no warranty|without warranty|disclaims", warranty):
                add(
                    "Warranty coverage appears limited or disclaimed",
                    "warranty_coverage",
                    "Clause suggests limited or no warranty protection.",
                )

        insurance = norm(facts.insurance_coverage)
        if insurance:
            if re.search(r"lessee responsible for all losses|self[- ]?insure", insurance):
                add(
                    "Insurance clause shifts all loss risk to lessee",
                    "insurance_coverage",
                    "Clause suggests full risk transfer without insurer coverage.",
                )

        # Mileage overage + allowance heuristics
        if facts.overage_fee_per_mile is not None:
            if facts.overage_fee_per_mile > Decimal("0.35"):
                add(
                    "Mileage overage fee appears high",
                    "overage_fee_per_mile",
                    f"Overage fee per mile is {facts.overage_fee_per_mile}.",
                )
        if facts.mileage_limit_per_year is not None:
            if facts.mileage_limit_per_year < 10000:
                add(
                    "Mileage allowance appears low",
                    "mileage_limit_per_year",
                    f"Annual mileage limit is {facts.mileage_limit_per_year}.",
                )

        # Maintenance responsibility heuristics
        if facts.maintenance_responsibility is not None:
            resp = facts.maintenance_responsibility
            if hasattr(resp, "value"):
                resp = resp.value
            resp = str(resp).lower()
            if resp == "lessee":
                add(
                    "Maintenance responsibility falls on lessee",
                    "maintenance_responsibility",
                    "Lessee is responsible for most or all maintenance.",
                )
            if resp == "shared":
                add(
                    "Maintenance responsibility is shared",
                    "maintenance_responsibility",
                    "Shared maintenance can introduce cost ambiguity.",
                )
        elif facts.maintenance_clause:
            clause = re.sub(r"\s+", " ", facts.maintenance_clause).lower()
            if "your expense" in clause or "at your own expense" in clause or "you agree to maintain" in clause:
                add(
                    "Maintenance responsibility falls on lessee",
                    "maintenance_clause",
                    "Clause indicates lessee pays for maintenance and repairs.",
                )

        return flags, explanations

    def _extract_money_amount(self, text: str) -> Optional[Decimal]:
        match = re.search(r"\$?\s*(\d{2,5}(?:,\d{3})*(?:\.\d{2})?)", text)
        if not match:
            return None
        raw = match.group(1).replace(",", "")
        try:
            return Decimal(raw)
        except Exception:
            return None

    def _extract_percent(self, text: str) -> Optional[Decimal]:
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if not match:
            return None
        try:
            return Decimal(match.group(1))
        except Exception:
            return None

    def _score_categorical(self, rule: Rule, value: Any) -> tuple[Decimal, str, Optional[str]]:
        if hasattr(value, "value"):
            value = value.value
        val = str(value).lower().strip()
        categories = rule.categories or {}
        raw = categories.get(val, Decimal("50"))
        score = _clamp(raw)
        flag = None
        if score < Decimal("40"):
            flag = f"{rule.field} category scored poorly"
        explanation = f"{rule.field} categorized as '{val}'"
        return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), explanation, flag

    def _score_boolean(self, rule: Rule, value: Any) -> tuple[Decimal, str, Optional[str]]:
        truthy = bool(value)
        score = Decimal("100") if truthy else Decimal("0")
        if rule.direction == Direction.LOWER_BETTER:
            score = Decimal("100") - score
        score = _clamp(score)
        flag = None
        if score < Decimal("40"):
            flag = f"{rule.field} boolean rule flagged"
        explanation = f"{rule.field} boolean evaluated as {truthy}"
        return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), explanation, flag
