"""
Contract Fairness Score Calculator

Evaluates a car lease/loan contract against market benchmarks and standard terms.
Produces a fairness score (0-100) and detailed analysis.
"""

import json
from typing import Dict, Any, Tuple
from .pricing_service import get_comprehensive_pricing


def parse_sla(sla_json: str) -> Dict[str, Any]:
    """
    Parse SLA JSON string safely.
    
    Args:
        sla_json: JSON string containing extracted SLA data
    
    Returns:
        Dictionary of parsed SLA or empty dict if parse fails
    """
    try:
        if isinstance(sla_json, str):
            return json.loads(sla_json)
        return sla_json if isinstance(sla_json, dict) else {}
    except Exception:
        return {}


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float safely."""
    try:
        if isinstance(value, str):
            # Remove common monetary symbols and text
            value = value.replace("$", "").replace("%", "").replace(",", "").strip()
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def evaluate_monthly_payment(monthly_payment: float, total_cost: float, lease_term_months: int) -> Tuple[int, str]:
    """
    Evaluate if monthly payment is fair relative to total cost.
    
    Returns:
        (score 0-25, reason)
    """
    if lease_term_months <= 0 or not monthly_payment:
        return 0, "Invalid lease term or payment"
    
    # Calculate implied monthly from total
    implied_monthly = total_cost / lease_term_months if lease_term_months > 0 else 0
    
    # Good if actual <= implied (or within 10%)
    if monthly_payment <= implied_monthly * 1.1:
        return 25, "Monthly payment competitive"
    elif monthly_payment <= implied_monthly * 1.2:
        return 15, "Monthly payment slightly high"
    else:
        return 5, "Monthly payment significantly higher than fair value"


def evaluate_interest_rate(interest_rate: float, credit_score: str = "average") -> Tuple[int, str]:
    """
    Evaluate if interest rate is competitive.
    
    Fair rates (2024):
    - Excellent credit (750+): 4-6%
    - Good credit (700-749): 6-8%
    - Average credit (650-699): 8-10%
    - Poor credit (<650): 10-15%+
    
    Returns:
        (score 0-15, reason)
    """
    if interest_rate <= 0:
        return 0, "No interest rate specified"
    
    rate_benchmarks = {
        "excellent": (4, 6),
        "good": (6, 8),
        "average": (8, 10),
        "poor": (10, 15)
    }
    
    benchmark = rate_benchmarks.get(credit_score.lower(), (8, 10))
    low, high = benchmark
    
    if interest_rate < low:
        return 15, "Interest rate excellent"
    elif interest_rate <= high:
        return 12, "Interest rate fair"
    elif interest_rate <= high + 2:
        return 8, "Interest rate higher than market"
    else:
        return 4, "Interest rate significantly above market"


def evaluate_mileage_allowance(annual_mileage_limit: float, lease_term_years: float) -> Tuple[int, str]:
    """
    Evaluate mileage limits (12,000 mi/year is standard).
    
    Returns:
        (score 0-15, reason)
    """
    if annual_mileage_limit <= 0 or lease_term_years <= 0:
        return 0, "Invalid mileage or lease term"
    
    total_allowed_miles = annual_mileage_limit * lease_term_years
    standard_miles = 12000 * lease_term_years
    
    if total_allowed_miles >= standard_miles * 0.95:
        return 15, "Mileage allowance standard or better"
    elif total_allowed_miles >= standard_miles * 0.85:
        return 10, "Mileage allowance slightly limited"
    else:
        return 5, "Mileage allowance restrictive"


def evaluate_early_termination(early_termination_fee: float, monthly_payment: float, months_remaining: int = 0) -> Tuple[int, str]:
    """
    Evaluate early termination fees (should not exceed 2-3 months of payments).
    
    Returns:
        (score 0-15, reason)
    """
    if early_termination_fee < 0:
        return 0, "Invalid early termination fee"
    
    if early_termination_fee == 0:
        return 15, "No early termination fee - excellent"
    
    if monthly_payment == 0:
        return 10, "Early termination fee present (fee can't be evaluated)"
    
    months_equivalent = early_termination_fee / monthly_payment if monthly_payment > 0 else 0
    
    if months_equivalent <= 2:
        return 15, "Early termination fee reasonable"
    elif months_equivalent <= 3.5:
        return 10, "Early termination fee moderate"
    else:
        return 5, "Early termination fee excessive"


def evaluate_penalties(penalty_amount: float = 0, has_late_fees: bool = False) -> Tuple[int, str]:
    """
    Evaluate penalty structure clarity and fairness.
    
    Returns:
        (score 0-10, reason)
    """
    if has_late_fees:
        if penalty_amount > 0 and penalty_amount <= 50:
            return 10, "Penalty structure clear and reasonable"
        elif penalty_amount > 0:
            return 6, "Penalty amounts appear excessive"
        else:
            return 8, "Penalties mentioned but amounts unclear"
    else:
        return 5, "Penalty structure not clearly defined"


def calculate_fairness_score(sla_json: str, vin: str = None) -> Dict[str, Any]:
    """
    Calculate overall Contract Fairness Score (0-100).
    
    Scoring breakdown:
    - Monthly Payment Evaluation: 25 points
    - Interest Rate: 15 points
    - Mileage Allowance: 15 points
    - Early Termination: 15 points
    - Penalty Structure: 10 points
    - Market Comparison: 20 points
    
    Args:
        sla_json: Extracted SLA data
        vin: Vehicle VIN for market comparison
    
    Returns:
        Dictionary with fairness score and detailed breakdown
    """
    sla = parse_sla(sla_json)
    
    # Extract SLA fields with safe conversion
    monthly_payment = safe_float(sla.get("monthly_payment", 0))
    total_cost = safe_float(sla.get("total_cost", 0))
    lease_term = safe_float(sla.get("lease_term", 0))
    interest_rate = safe_float(sla.get("interest_rate", 0))
    mileage_limit = safe_float(sla.get("mileage_limit", 0))
    early_termination = safe_float(sla.get("early_termination", 0))
    penalties = safe_float(sla.get("penalties", 0))
    
    lease_term_months = lease_term * 12 if lease_term > 0 else 36
    lease_term_years = lease_term if lease_term > 0 else 3
    
    # Calculate component scores
    payment_score, payment_reason = evaluate_monthly_payment(monthly_payment, total_cost, lease_term_months)
    rate_score, rate_reason = evaluate_interest_rate(interest_rate)
    mileage_score, mileage_reason = evaluate_mileage_allowance(mileage_limit, lease_term_years)
    termination_score, termination_reason = evaluate_early_termination(early_termination, monthly_payment)
    penalty_score, penalty_reason = evaluate_penalties(penalties, bool(sla.get("penalties")))
    
    # Market comparison (if VIN provided)
    market_score = 0
    market_reason = "Pricing data not available"
    
    if vin:
        try:
            pricing = get_comprehensive_pricing(vin)
            if "error" not in pricing:
                fair_value = pricing.get("average_fair_value", 0)
                if fair_value > 0 and monthly_payment > 0:
                    # Estimate total cost if not provided
                    est_total = monthly_payment * lease_term_months
                    
                    if est_total <= fair_value * 1.15:  # Within 15% of fair value
                        market_score = 20
                        market_reason = "Price competitive vs. market"
                    elif est_total <= fair_value * 1.35:  # Within 35%
                        market_score = 12
                        market_reason = "Price slightly above market"
                    else:
                        market_score = 5
                        market_reason = "Price significantly above market value"
        except Exception:
            market_score = 0
            market_reason = "Market comparison unavailable"
    
    # Calculate total fairness score
    total_score = (
        payment_score +
        rate_score +
        mileage_score +
        termination_score +
        penalty_score +
        market_score
    )
    
    # Normalize to 0-100
    fairness_score = min(100, max(0, total_score))
    
    # Determine fairness level
    if fairness_score >= 80:
        fairness_level = "EXCELLENT"
    elif fairness_score >= 65:
        fairness_level = "GOOD"
    elif fairness_score >= 50:
        fairness_level = "FAIR"
    elif fairness_score >= 35:
        fairness_level = "POOR"
    else:
        fairness_level = "VERY POOR"
    
    return {
        "fairness_score": fairness_score,
        "fairness_level": fairness_level,
        "breakdown": {
            "monthly_payment": {
                "score": payment_score,
                "max": 25,
                "reason": payment_reason
            },
            "interest_rate": {
                "score": rate_score,
                "max": 15,
                "reason": rate_reason
            },
            "mileage_allowance": {
                "score": mileage_score,
                "max": 15,
                "reason": mileage_reason
            },
            "early_termination": {
                "score": termination_score,
                "max": 15,
                "reason": termination_reason
            },
            "penalty_structure": {
                "score": penalty_score,
                "max": 10,
                "reason": penalty_reason
            },
            "market_comparison": {
                "score": market_score,
                "max": 20,
                "reason": market_reason
            }
        },
        "recommendations": generate_recommendations(sla, fairness_score)
    }


def generate_recommendations(sla: Dict[str, Any], fairness_score: float) -> list:
    """
    Generate actionable recommendations based on fairness analysis.
    """
    recommendations = []
    
    if fairness_score < 60:
        recommendations.append("⚠️ Consider declining this contract and exploring alternatives")
    
    if safe_float(sla.get("interest_rate", 0)) > 10:
        recommendations.append("🔴 Extremely high interest rate - negotiate or seek better financing")
    
    if safe_float(sla.get("mileage_limit", 0)) < 10000:
        recommendations.append("🔴 Mileage limit significantly below standard 12,000/year")
    
    if safe_float(sla.get("early_termination", 0)) > safe_float(sla.get("monthly_payment", 0)) * 3:
        recommendations.append("🟡 Early termination fees are high - consider Gap Insurance")
    
    if safe_float(sla.get("penalties", 0)) > 100:
        recommendations.append("🟡 Late fees are substantial - ensure timely payments")
    
    if not recommendations:
        recommendations.append("✅ Contract terms appear reasonable - proceed with confidence")
    
    return recommendations
