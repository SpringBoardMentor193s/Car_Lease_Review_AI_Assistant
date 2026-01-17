import json
from backend.schemas.sla_schema import SLA_FIELDS

def extract_sla_with_llm(text: str) -> dict:
    """
    Placeholder LLM extractor.
    For now, we simulate LLM output structure.
    API integration will be added next.
    """

    # Copy schema to ensure all fields exist
    sla_data = SLA_FIELDS.copy()

    # ⚠️ LLM NOT CONNECTED YET
    # This is intentional (mentor-friendly stepwise build)

    # Example simulated extraction (to test pipeline)
    # In real LLM call, this JSON will come from model response
    simulated_llm_output = {
        "down_payment": "5000",
        "mileage_limit": "12000 miles/year",
        "late_fees": "2% per month",
        "buyout_price": "15000"
    }

    # Merge simulated data
    for key, value in simulated_llm_output.items():
        sla_data[key] = value

    return sla_data
