import re

def _parse_money(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = value.replace(",", "")
    match = re.search(r"[\d.]+", value)
    return float(match.group()) if match else None


def calculate_fairness(contract_sla: dict, price_estimate: dict):
    """
    Rule-based, explainable fairness score (0–100)
    """

    score = 100
    reasons = []

    est_min = price_estimate.get("estimated_min")
    est_max = price_estimate.get("estimated_max")

    monthly_payment = _parse_money(contract_sla.get("Monthly Payment"))
    apr = _parse_money(contract_sla.get("APR"))

    #Market price unavailable
    if not est_min or not est_max:
        return {
            "score": "unknown",
            "reason": "price_estimation_not_available"
        }

    # High implied cost
    if monthly_payment and monthly_payment * 36 > est_max:
        score -= 25
        reasons.append("Effective cost exceeds market range")

    #High APR
    if apr and apr > 7:
        score -= 15
        reasons.append("High interest rate")

    # Early termination penalty
    if contract_sla.get("Early Termination Penalty"):
        score -= 15
        reasons.append("Strict early termination penalty")

    # Clamp score
    score = max(0, min(100, score))

    return {
        "score": score,
        "reasons": reasons if reasons else ["Deal appears reasonable"]
    }
