def analyze_contract(text):
    risk = "Low"
    suggestions = []

    # Interest rate check
    if "Interest Rate" in text or "APR" in text:
        suggestions.append("Negotiate interest rate as it may be higher than market average.")
        risk = "Medium"

    # Early termination check
    if "termination" in text.lower():
        suggestions.append("Request reduction in early termination penalties.")
        risk = "Medium"

    # Mileage check
    if "Excess Mileage" in text or "mileage" in text.lower():
        suggestions.append("Negotiate higher mileage limit or lower excess mileage charges.")

    # Default safety
    if len(suggestions) == 0:
        suggestions.append("Contract terms look reasonable. Minor negotiation recommended.")

    return {
        "risk": risk,
        "suggestions": suggestions
    }
