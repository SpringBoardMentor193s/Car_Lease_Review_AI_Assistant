import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are an extraction assistant. Return ONLY valid JSON with keys: "
    "APR, TermMonths, MonthlyPayment, DownPayment, ResidualValue, MileageAllowancePerYear, "
    "MileageOverageFee, EarlyTerminationFee, PurchaseOptionPrice, InsuranceRequirements, "
    "MaintenanceResponsibilities, WarrantySummary, LateFeePolicy, OtherTerms."
)

def regex_fallback(contract_text: str) -> dict:
    """Fallback extractor using regex when GPT fails or quota is exceeded."""
    return {
        "APR": re.search(r"APR[:\s]*([\d\.]+%)", contract_text).group(1) if re.search(r"APR[:\s]*([\d\.]+%)", contract_text) else None,
        "TermMonths": re.search(r"Lease Term[:\s]*(\d+)", contract_text).group(1) if re.search(r"Lease Term[:\s]*(\d+)", contract_text) else None,
        "MonthlyPayment": re.search(r"Monthly Payment[:\s]*\$(\d+)", contract_text).group(1) if re.search(r"Monthly Payment[:\s]*\$(\d+)", contract_text) else None,
        "DownPayment": None,  # not in sample text
        "ResidualValue": None,
        "MileageAllowancePerYear": re.search(r"Mileage Limit[:\s]*([\d,]+)", contract_text).group(1) if re.search(r"Mileage Limit[:\s]*([\d,]+)", contract_text) else None,
        "MileageOverageFee": None,
        "EarlyTerminationFee": None,
        "PurchaseOptionPrice": None,
        "InsuranceRequirements": None,
        "MaintenanceResponsibilities": None,
        "WarrantySummary": None,
        "LateFeePolicy": None,
        "OtherTerms": None
    }

def extract_sla_terms(contract_text: str):
    prompt = f"""
    Extract the following fields from this car lease contract:
    - APR
    - TermMonths
    - MonthlyPayment
    - DownPayment
    - ResidualValue
    - MileageAllowancePerYear
    - MileageOverageFee
    - EarlyTerminationFee
    - PurchaseOptionPrice
    - InsuranceRequirements
    - MaintenanceResponsibilities
    - WarrantySummary
    - LateFeePolicy
    - OtherTerms

    Return ONLY JSON, no commentary.

    Contract:
    {contract_text}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",  # fallback model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0
        )
        content = resp.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"⚠️ GPT call failed: {e}")
        print("➡️ Using regex fallback for SLA extraction...")
        return regex_fallback(contract_text)