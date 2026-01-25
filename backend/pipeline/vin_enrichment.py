from backend.app.services.nhtsa_service import decode_vin

def enrich_with_vehicle_data(sla_json: dict):
    """
    Extract VIN from SLA JSON and fetch vehicle details.
    """
    # Safety Check: Ensure sla_json is actually a dictionary
    if not isinstance(sla_json, dict):
        print(f"Error: Expected dict for vin_enrichment, got {type(sla_json)}")
        return {"error": "Invalid data format passed to VIN enrichment"}

    vin = sla_json.get("VIN")
    
    # Check if VIN exists and is not 'null' (common AI output)
    if not vin or vin == "null":
        return {"warning": "No VIN found in contract to verify."}

    return decode_vin(vin)
