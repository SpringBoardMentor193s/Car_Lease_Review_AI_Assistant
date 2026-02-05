def calculate_fairness_score(
    sla_data: dict,
    risk_data: dict,
    vehicle_data: dict | None,
    recall_data: dict | None,
    safety_rating: dict | None
):
    score = 100
    reasons = []

    # ---------- FINANCIAL FAIRNESS ----------

    if sla_data.get("down_payment"):
        try:
            if float(sla_data["down_payment"]) > 4000:
                score -= 10
                reasons.append("High upfront down payment")
        except:
            pass

    if sla_data.get("late_fees"):
        score -= 10
        reasons.append("Late payment penalties present")

    if sla_data.get("interest_rate"):
        try:
            if float(sla_data["interest_rate"]) > 8:
                score -= 15
                reasons.append("High interest rate")
        except:
            pass

    # ---------- USAGE FAIRNESS ----------

    if sla_data.get("mileage_limit"):
        score -= 10
        reasons.append("Restrictive mileage limit")

    # ---------- VEHICLE VALUE FAIRNESS ----------

    if vehicle_data and vehicle_data.get("Model Year"):
        try:
            year = int(vehicle_data["Model Year"])
            if year < 2015:
                score -= 10
                reasons.append("Older vehicle for lease terms")
        except:
            pass

    # ---------- SAFETY & RECALL FAIRNESS ----------

    if recall_data and recall_data.get("total_recalls", 0) > 0:
        score -= 10
        reasons.append("Vehicle has recall history")

    if safety_rating:
        try:
            stars = int(safety_rating.get("overall_rating", 0))
            if stars and stars <= 3:
                score -= 10
                reasons.append("Low safety rating")
        except:
            pass

    # ---------- FINAL SCORE NORMALIZATION ----------

    score = max(0, min(score, 100))

    if score >= 80:
        category = "FAIR"
    elif score >= 60:
        category = "MODERATELY UNFAIR"
    else:
        category = "HIGHLY UNFAIR"

    return {
        "fairness_score": score,
        "fairness_category": category,
        "fairness_reasons": reasons,
        "summary": f"This contract is classified as {category.lower()} based on lease terms and vehicle factors."
    }
