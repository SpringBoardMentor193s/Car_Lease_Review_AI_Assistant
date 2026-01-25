def build_final_response(sla_data, vehicle_data):
    """
    Combine SLA extraction and vehicle verification into a single object.
    """
    # Create a structured response for the Frontend
    return {
        "status": "success" if vehicle_data and "error" not in vehicle_data else "partial_success",
        "contract_analysis": sla_data,
        "vehicle_details": vehicle_data,
        "summary": {
            "monthly_payment": sla_data.get("Monthly Payment"),
            "vin_verified": "Make" in str(vehicle_data)
        }
    }