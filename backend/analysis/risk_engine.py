def calculate_lease_risk(sla_data: dict, vehicle_data: dict | None):
    score = 0
    reasons = []

    if sla_data.get("late_fees"):
        score += 2
        reasons.append("Late fees present")

    if sla_data.get("early_termination"):
        score += 2
        reasons.append("Early termination clause")

    if sla_data.get("down_payment"):
        score += 1
        reasons.append("High upfront payment")

    if sla_data.get("mileage_limit"):
        score += 1
        reasons.append("Mileage restriction")

    if vehicle_data and vehicle_data.get("Model Year"):
        year = int(vehicle_data["Model Year"])
        if year < 2015:
            score += 1
            reasons.append("Older vehicle")

    if score <= 2:
        level = "LOW RISK"
    elif score <= 4:
        level = "MEDIUM RISK"
    else:
        level = "HIGH RISK"

    return {
        "risk_level": level,
        "risk_score": score,
        "reasons": reasons
    }
