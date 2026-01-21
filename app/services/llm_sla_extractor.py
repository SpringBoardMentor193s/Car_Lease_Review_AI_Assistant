import json
import re
from app.models.sla_schema import SLASummary


def mock_llm_response(text: str) -> dict:
    """
    Simulates an LLM JSON response for SLA extraction
    """

    return {
        "interest_rate_apr": 8.5,
        "lease_term_months": 36,
        "monthly_payment": 25000,
        "down_payment": 150000,
        "residual_value": 600000,
        "purchase_option_price": 620000,
        "mileage_allowance_km_per_year": 12000,
        "mileage_overage_fee_per_km": 10,
        "early_termination_clause": "Early termination incurs penalty of 3 months payments",
        "maintenance_responsibility": "Lessee responsible for routine maintenance",
        "warranty_coverage": "Covered under manufacturer warranty for 3 years",
        "insurance_requirement": "Comprehensive insurance required",
        "late_fee_penalties": "₹1500 per day after 7 days grace",
        "red_flags": ["Severe early termination penalty"],
        "fairness_score": 80,
        "confidence_score": 0.92
    }


def extract_sla_llm_based(text: str) -> SLASummary:
    """
    Mock LLM-based SLA extraction
    """

    llm_json = mock_llm_response(text)

    sla = SLASummary(
        interest_rate_apr=llm_json["interest_rate_apr"],
        lease_term_months=llm_json["lease_term_months"],
        monthly_payment=llm_json["monthly_payment"],
        down_payment=llm_json["down_payment"],
        residual_value=llm_json["residual_value"],
        purchase_option_price=llm_json["purchase_option_price"],
        mileage_allowance_km_per_year=llm_json["mileage_allowance_km_per_year"],
        mileage_overage_fee_per_km=llm_json["mileage_overage_fee_per_km"],
        early_termination_clause=llm_json["early_termination_clause"],
        maintenance_responsibility=llm_json["maintenance_responsibility"],
        warranty_coverage=llm_json["warranty_coverage"],
        insurance_requirement=llm_json["insurance_requirement"],
        late_fee_penalties=llm_json["late_fee_penalties"],
        red_flags=llm_json["red_flags"],
        fairness_score=llm_json["fairness_score"],
    )

    return sla
