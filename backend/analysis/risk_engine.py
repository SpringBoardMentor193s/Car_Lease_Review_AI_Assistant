def calculate_lease_risk(
    sla_data: dict,
    vehicle_data: dict | None,
    recall_data: dict | None,
    safety_rating: dict | None = None
):
    score = 0
    reasons = []
    categories = []

    # ---------- SLA BASED RISK ----------

    if sla_data.get("late_fees"):
        score += 2
        reasons.append("Late fees present")
        categories.append("Financial")

    if sla_data.get("early_termination"):
        score += 2
        reasons.append("Early termination clause")
        categories.append("Legal")

    if sla_data.get("down_payment"):
        try:
            dp = float(sla_data["down_payment"])
            if dp > 4000:
                score += 1
                reasons.append("High upfront payment")
                categories.append("Financial")
        except:
            pass

    if sla_data.get("mileage_limit"):
        score += 1
        reasons.append("Mileage restriction")
        categories.append("Usage")

    # ---------- VEHICLE AGE RISK ----------

    if vehicle_data and vehicle_data.get("Model Year"):
        try:
            year = int(vehicle_data["Model Year"])
            if year < 2015:
                score += 1
                reasons.append("Older vehicle")
                categories.append("Vehicle")
        except:
            pass

    # ---------- RECALL SAFETY RISK ----------

    if recall_data:
        total = recall_data.get("total_recalls", 0)
        open_recalls = recall_data.get("open_recalls", 0)

        if total > 0:
            score += 1
            reasons.append(f"{total} recalls in vehicle history")
            categories.append("Safety")

        if open_recalls > 0:
            score += 2
            reasons.append(f"{open_recalls} OPEN recalls (unfixed)")
            categories.append("Critical Safety")

    # ---------- SAFETY RATING RISK ----------

    if safety_rating:
        try:
            stars = int(safety_rating.get("overall_rating", 0))
            if stars and stars <= 3:
                score += 2
                reasons.append("Low safety rating")
                categories.append("Safety")
        except:
            pass

    # ---------- FINAL RISK LEVEL ----------

    if score <= 2:
        level = "LOW RISK"
    elif score <= 5:
        level = "MEDIUM RISK"
    else:
        level = "HIGH RISK"

    # ---------- RISK BREAKDOWN (DASHBOARD READY) ----------

    breakdown = {
        "financial_risk": categories.count("Financial"),
        "legal_risk": categories.count("Legal"),
        "usage_risk": categories.count("Usage"),
        "vehicle_risk": categories.count("Vehicle"),
        "safety_risk": categories.count("Safety") + categories.count("Critical Safety")
    }

    # ---------- CONFIDENCE SCORE ----------

    confidence = min(0.95, 0.6 + (score * 0.05))

    # ---------- HUMAN BUSINESS SUMMARY ----------

    if level == "HIGH RISK":
        summary = (
            "This lease agreement presents a high financial and legal risk profile. "
            "Key contributing factors include " + ", ".join(reasons[:3]) +
            ". Careful review is recommended before approval."
        )
    elif level == "MEDIUM RISK":
        summary = (
            "This lease shows a moderate risk profile driven mainly by " +
            ", ".join(reasons[:3]) +
            ". Additional verification may reduce exposure."
        )
    else:
        summary = (
            "This lease appears to be low risk with no major financial, legal, or safety concerns identified."
        )

    # ---------- FINAL OUTPUT ----------

    return {
        "risk_level": level,
        "risk_score": score,
        "confidence": round(confidence, 2),
        "risk_categories": list(set(categories)),
        "risk_breakdown": breakdown,
        "reasons": reasons,
        "summary": summary
    }
