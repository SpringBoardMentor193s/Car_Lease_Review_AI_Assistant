def generate_lease_advice(risk_data: dict):
    advice = []

    if "Late fees present" in risk_data["reasons"]:
        advice.append("Consider negotiating lower late fee penalties.")

    if "Early termination clause" in risk_data["reasons"]:
        advice.append("Review early termination terms carefully to avoid heavy penalties.")

    if "High upfront payment" in risk_data["reasons"]:
        advice.append("High down payment detected — you may reduce initial financial burden by renegotiating.")

    if any("recall" in r.lower() for r in risk_data["reasons"]):
        advice.append("Vehicle has recall history — verify recall repairs before signing.")

    if risk_data["risk_level"] == "HIGH RISK":
        advice.append("Overall risk is high — legal or financial review is strongly recommended.")

    return advice
