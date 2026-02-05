import re

# Static benchmark prices (INR, example ranges)
STATIC_BENCHMARKS = {
    "HONDA_2024": {"min": 1400000, "max": 1800000},
    "HONDA_2023": {"min": 1300000, "max": 1700000},
    "TOYOTA_2024": {"min": 1500000, "max": 1900000}
}

def _parse_money(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = value.replace(",", "")
    match = re.search(r"[\d.]+", value)
    return float(match.group()) if match else None


def estimate_price(sla_data: dict, vehicle_data: dict | None = None):
    """
    Hybrid price estimation:
    1. Lease math heuristic
    2. Static benchmark fallback
    """

    monthly_payment = _parse_money(sla_data.get("Monthly Payment"))
    residual_value = _parse_money(sla_data.get("Residual Value"))
    term = _parse_money(sla_data.get("Loan Term"))

    # Tier 1: Lease heuristic
 
    if monthly_payment and residual_value and term:
        # Reasonable money factor range (≈ 2.4%–7.2% APR)
        money_factor = 0.002  

        # Reverse lease formula to estimate capitalized cost
        cap_cost = (
            (monthly_payment * term + residual_value)
            / (1 + money_factor * term)
        )

        return {
            "estimated_min": round(cap_cost * 0.9),
            "estimated_max": round(cap_cost * 1.1),
            "source": "lease_heuristic"
        }

    # Tier 2: Static benchmark
    
    if vehicle_data:
        key = f"{vehicle_data.get('Make')}_{vehicle_data.get('ModelYear')}"
        if key in STATIC_BENCHMARKS:
            return {
                **STATIC_BENCHMARKS[key],
                "source": "static_benchmark"
            }

    # Tier 3: Unknown (safe)
  
    return {
    "estimated_min": STATIC_BENCHMARKS[key]["min"],
    "estimated_max": STATIC_BENCHMARKS[key]["max"],
    "source": "static_benchmark"
}
