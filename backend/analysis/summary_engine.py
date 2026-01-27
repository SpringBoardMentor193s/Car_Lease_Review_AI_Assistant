def generate_contract_summary(sla_data, vehicle_data, recall_data, risk_assessment):
    overview = f"This is a {sla_data.get('lease_term_months')} month lease agreement for a {vehicle_data.get('Model Year')} {vehicle_data.get('Make')} {vehicle_data.get('Model')}."

    financial = f"The monthly payment is {sla_data.get('monthly_payment')} with a down payment of {sla_data.get('down_payment')} and interest rate {sla_data.get('interest_rate')}%."

    vehicle = f"The vehicle has {recall_data.get('total_recalls')} historical recalls and is considered an older model."

    risk = f"The overall lease risk is classified as {risk_assessment.get('risk_level')}."

    recommendation = risk_assessment.get("summary")

    return {
        "overview": overview,
        "financial_terms": financial,
        "vehicle_insights": vehicle,
        "risk_evaluation": risk,
        "recommendation": recommendation
    }
