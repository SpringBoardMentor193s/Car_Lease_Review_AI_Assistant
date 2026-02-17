"""
Rule-driven fairness scoring engine.
"""

import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

from models.contract_facts import ContractFacts
from models.fairness_report import FairnessReport, Verdict
from models.scoring_rules import ScoringRules, Rule, ScoringMethod, Direction
from engine.market_pricing import MarketPricingClient

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
        self.market_pricing = MarketPricingClient()

    def score(self, facts: ContractFacts) -> FairnessReport:
        subscores: Dict[str, Decimal] = {}
        explanations: Dict[str, str] = {}
        red_flags = []
        pricing_estimation_context: Dict[str, Any] = {}

        buyout_rule = None
        for rule_name, rule in self.rules.rules.items():
            if rule.field == "buyout_price":
                buyout_rule = (rule_name, rule)
                continue
            value = getattr(facts, rule.field, None)
            score, explanation, flag = self._score_rule(
                rule,
                value,
                facts,
                subscores,
                pricing_estimation_context,
            )
            subscores[rule_name] = score
            if explanation:
                explanations[rule_name] = explanation
            if flag:
                red_flags.append(flag)

        if buyout_rule:
            rule_name, rule = buyout_rule
            value = getattr(facts, rule.field, None)
            score, explanation, flag = self._score_rule(
                rule,
                value,
                facts,
                subscores,
                pricing_estimation_context,
            )
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
        recommendations = self._build_recommendations(facts, pricing_estimation_context)

        return FairnessReport(
            overall_score=overall_score,
            verdict=verdict,
            subscores=subscores,
            red_flags=red_flags,
            explanations=explanations,
            pricing_estimation_context=pricing_estimation_context,
            recommended_price_range=recommendations["recommended_price_range"],
            recommended_lease_deal=recommendations["recommended_lease_deal"],
            recommended_terms=recommendations["recommended_terms"],
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

    def _score_rule(
        self,
        rule: Rule,
        value: Any,
        facts: ContractFacts,
        context_subscores: Dict[str, Decimal],
        pricing_estimation_context: Dict[str, Any],
    ) -> tuple[Decimal, str, Optional[str]]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return Decimal("50"), f"{rule.field} not found; default score applied", None

        if rule.method == ScoringMethod.Z_SCORE:
            return self._score_z(
                rule,
                value,
                facts,
                context_subscores,
                pricing_estimation_context,
            )
        if rule.method == ScoringMethod.CATEGORICAL_MAP:
            return self._score_categorical(rule, value)
        if rule.method == ScoringMethod.BOOLEAN_RULE:
            return self._score_boolean(rule, value)

        return Decimal("50"), f"Unknown method for {rule.field}; default score applied", None

    def _score_z(
        self,
        rule: Rule,
        value: Any,
        facts: ContractFacts,
        context_subscores: Dict[str, Decimal],
        pricing_estimation_context: Dict[str, Any],
    ) -> tuple[Decimal, str, Optional[str]]:
        val = _to_decimal(value)
        if val is None:
            return Decimal("50"), f"{rule.field} value invalid; default score applied", None

        benchmark, dynamic_note, benchmark_context = self._resolve_benchmark(
            rule.field,
            facts,
            context_subscores,
        )
        if benchmark_context:
            pricing_estimation_context.update(benchmark_context)
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
        if dynamic_note:
            explanation = f"{explanation}. {dynamic_note}"
        return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), explanation, flag

    def _resolve_benchmark(
        self,
        field: str,
        facts: ContractFacts,
        context_subscores: Dict[str, Decimal],
    ) -> Tuple[Dict[str, Decimal], Optional[str], Optional[Dict[str, Any]]]:
        if field != "buyout_price":
            return self.benchmarks.get(field, {}), None, None

        online = self.market_pricing.fetch_buyout_benchmark(facts)
        if online:
            context = self._build_pricing_context(
                facts=facts,
                source="marketcheck_online" if self.market_pricing.provider == "marketcheck" else "online_market_api",
                benchmark=online,
            )
            return online, (
                "Online market benchmark applied for buyout price using live location and condition comparables."
            ), context

        default_benchmark = self.benchmarks.get(field, {})
        dynamic = self._build_dynamic_buyout_benchmark(facts, context_subscores, default_benchmark)
        context = self._build_pricing_context(
            facts=facts,
            source="fallback_formula",
            benchmark=dynamic["benchmark"],
        )
        return dynamic["benchmark"], dynamic["note"], context

    def _build_dynamic_buyout_benchmark(
        self,
        facts: ContractFacts,
        context_subscores: Dict[str, Decimal],
        default_benchmark: Dict[str, Any],
    ) -> Dict[str, Any]:
        base_mean = _to_decimal(default_benchmark.get("mean")) or Decimal("15000")

        weighted_sum = base_mean * Decimal("0.35")
        total_weight = Decimal("0.35")

        if facts.residual_value_amount is not None:
            weighted_sum += facts.residual_value_amount * Decimal("0.45")
            total_weight += Decimal("0.45")

        payment_total = facts.monthly_payment * Decimal(str(facts.lease_term_months))
        if facts.down_payment is not None:
            payment_total += facts.down_payment

        lease_signal = payment_total * Decimal("0.45")
        weighted_sum += lease_signal * Decimal("0.20")
        total_weight += Decimal("0.20")

        if facts.residual_value_percent is not None:
            residual_signal = payment_total * (facts.residual_value_percent / Decimal("100"))
            weighted_sum += residual_signal * Decimal("0.20")
            total_weight += Decimal("0.20")

        mean = weighted_sum / total_weight if total_weight else base_mean

        context_score = self._safe_average(context_subscores)
        fairness_multiplier = Decimal("1.00")
        if context_score is not None:
            if context_score < Decimal("50"):
                fairness_multiplier = Decimal("0.92")
            elif context_score < Decimal("65"):
                fairness_multiplier = Decimal("0.97")
            elif context_score > Decimal("80"):
                fairness_multiplier = Decimal("1.03")

        adjusted_mean = mean * fairness_multiplier
        std = max(Decimal("1200"), adjusted_mean * Decimal("0.22"))
        min_val = max(Decimal("1000"), adjusted_mean - (std * Decimal("2")))
        max_val = adjusted_mean + (std * Decimal("2"))

        benchmark = {
            "mean": adjusted_mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "std": std.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "min": min_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "max": max_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }

        note = (
            "Fallback dynamic benchmark applied for buyout price using lease economics"
            f" (context_score={context_score if context_score is not None else 'n/a'})."
        )
        return {"benchmark": benchmark, "note": note}

    def _safe_average(self, subscores: Dict[str, Decimal]) -> Optional[Decimal]:
        if not subscores:
            return None
        total = sum(subscores.values(), Decimal("0"))
        return total / Decimal(str(len(subscores)))

    def _build_pricing_context(
        self,
        facts: ContractFacts,
        source: str,
        benchmark: Dict[str, Decimal],
    ) -> Dict[str, Any]:
        def as_float(v: Any) -> Optional[float]:
            d = _to_decimal(v)
            return float(d) if d is not None else None

        return {
            "field": "buyout_price",
            "source": source,
            "vin_used": facts.vin,
            "vehicle_identity": {
                "year": facts.vehicle_year,
                "make": facts.vehicle_make,
                "model": facts.vehicle_model,
            },
            "lessee_location": {
                "city": facts.lessee_city,
                "state": facts.lessee_state,
                "zip": facts.lessee_zip,
                "region": facts.lease_region,
            },
            "vehicle_condition": facts.vehicle_condition,
            "benchmark_used": {
                "mean": as_float(benchmark.get("mean")),
                "std": as_float(benchmark.get("std")),
                "min": as_float(benchmark.get("min")),
                "max": as_float(benchmark.get("max")),
            },
        }

    def _build_recommendations(
        self,
        facts: ContractFacts,
        pricing_estimation_context: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        buyout_benchmark = pricing_estimation_context.get("benchmark_used", {})
        buyout_min = _to_decimal(buyout_benchmark.get("min"))
        buyout_max = _to_decimal(buyout_benchmark.get("max"))
        buyout_mean = _to_decimal(buyout_benchmark.get("mean"))

        if buyout_min is None and buyout_mean is not None:
            buyout_min = buyout_mean * Decimal("0.85")
        if buyout_max is None and buyout_mean is not None:
            buyout_max = buyout_mean * Decimal("1.15")

        apr_benchmark = self.benchmarks.get("apr", {})
        apr_mean = _to_decimal(apr_benchmark.get("mean"))
        apr_std = _to_decimal(apr_benchmark.get("std")) or Decimal("1")
        apr_target_max = (apr_mean + (apr_std * Decimal("0.5"))) if apr_mean is not None else None

        monthly_benchmark = self.benchmarks.get("monthly_payment", {})
        monthly_mean = _to_decimal(monthly_benchmark.get("mean"))
        monthly_std = _to_decimal(monthly_benchmark.get("std")) or Decimal("1")
        monthly_low = (monthly_mean - monthly_std) if monthly_mean is not None else None
        monthly_high = (monthly_mean + monthly_std) if monthly_mean is not None else None

        def as_money(value: Optional[Decimal]) -> Optional[float]:
            if value is None:
                return None
            return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        def as_rate(value: Optional[Decimal]) -> Optional[float]:
            if value is None:
                return None
            return float(value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))

        recommended_price_range = {
            "field": "buyout_price",
            "label": "purchase_option_buyout_price",
            "currency": "USD",
            "fair_low": as_money(buyout_min),
            "fair_high": as_money(buyout_max),
            "fair_target": as_money(buyout_mean),
            "basis": pricing_estimation_context.get("source", "fallback_formula"),
        }

        recommended_lease_deal = {
            "target_apr_max_percent": as_rate(apr_target_max),
            "target_monthly_payment_range": {
                "low": as_money(monthly_low),
                "high": as_money(monthly_high),
            },
            "target_buyout_price_range": {
                "low": as_money(buyout_min),
                "high": as_money(buyout_max),
                "target": as_money(buyout_mean),
            },
            "current_contract_snapshot": {
                "apr_percent": as_rate(facts.apr),
                "monthly_payment": as_money(facts.monthly_payment),
                "buyout_price": as_money(facts.buyout_price),
            },
        }

        recommended_terms = {
            "apr": self._build_apr_recommendation(
                current_apr=facts.apr,
                apr_mean=apr_mean,
                apr_std=apr_std,
            ),
            "monthly_payment": self._build_monthly_payment_recommendation(
                current_monthly=facts.monthly_payment,
                monthly_mean=monthly_mean,
                monthly_std=monthly_std,
            ),
            "buyout_price": self._build_buyout_recommendation(
                current_buyout=facts.buyout_price,
                buyout_min=buyout_min,
                buyout_max=buyout_max,
                buyout_mean=buyout_mean,
                source=pricing_estimation_context.get("source", "fallback_formula"),
            ),
        }

        return {
            "recommended_price_range": recommended_price_range,
            "recommended_lease_deal": recommended_lease_deal,
            "recommended_terms": recommended_terms,
        }

    def _build_apr_recommendation(
        self,
        current_apr: Optional[Decimal],
        apr_mean: Optional[Decimal],
        apr_std: Decimal,
    ) -> Dict[str, Any]:
        if apr_mean is None:
            return {
                "current": float(current_apr) if current_apr is not None else None,
                "recommended": None,
                "range": {"low": None, "high": None},
                "unit": "percent",
                "source": "benchmark_static",
                "confidence": "low",
                "why": "APR benchmark unavailable.",
            }

        low = max(Decimal("0"), apr_mean - apr_std)
        high = apr_mean + (apr_std * Decimal("0.5"))
        recommended = min(apr_mean, high)
        current = current_apr if current_apr is not None else apr_mean

        confidence = "medium"
        why = "APR target based on benchmark mean and spread."
        if current_apr is not None and current_apr > high:
            why = "Current APR is above benchmark; target is within fair benchmark band."

        return {
            "current": float(current.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
            "recommended": float(recommended.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
            "range": {
                "low": float(low.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
                "high": float(high.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
            },
            "unit": "percent",
            "source": "benchmark_static",
            "confidence": confidence,
            "why": why,
        }

    def _build_monthly_payment_recommendation(
        self,
        current_monthly: Optional[Decimal],
        monthly_mean: Optional[Decimal],
        monthly_std: Decimal,
    ) -> Dict[str, Any]:
        if monthly_mean is None:
            return {
                "current": float(current_monthly) if current_monthly is not None else None,
                "recommended": None,
                "range": {"low": None, "high": None},
                "unit": "USD/month",
                "source": "benchmark_static",
                "confidence": "low",
                "why": "Monthly payment benchmark unavailable.",
            }

        low = max(Decimal("0"), monthly_mean - monthly_std)
        high = monthly_mean + monthly_std
        recommended = monthly_mean
        current = current_monthly if current_monthly is not None else monthly_mean

        why = "Monthly payment target based on benchmark range for similar lease structures."
        if current_monthly is not None and current_monthly > high:
            why = "Current monthly payment is above benchmark high; target set near benchmark mean."
        elif current_monthly is not None and current_monthly < low:
            why = "Current monthly payment is below benchmark low; likely favorable versus market."

        return {
            "current": float(current.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "recommended": float(recommended.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "range": {
                "low": float(low.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "high": float(high.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            },
            "unit": "USD/month",
            "source": "benchmark_static",
            "confidence": "medium",
            "why": why,
        }

    def _build_buyout_recommendation(
        self,
        current_buyout: Optional[Decimal],
        buyout_min: Optional[Decimal],
        buyout_max: Optional[Decimal],
        buyout_mean: Optional[Decimal],
        source: str,
    ) -> Dict[str, Any]:
        confidence = "high" if source in {"marketcheck_online", "online_market_api"} else "medium"
        why = "Buyout target derived from live market comparables." if confidence == "high" else (
            "Buyout target derived from dynamic fallback benchmark."
        )
        current = current_buyout if current_buyout is not None else buyout_mean

        def money(v: Optional[Decimal]) -> Optional[float]:
            if v is None:
                return None
            return float(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        return {
            "current": money(current),
            "recommended": money(buyout_mean),
            "range": {"low": money(buyout_min), "high": money(buyout_max)},
            "unit": "USD",
            "source": source,
            "confidence": confidence,
            "why": why,
        }

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
