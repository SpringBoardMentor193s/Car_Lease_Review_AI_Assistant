import os
import json
import requests
import re
from dotenv import load_dotenv
from backend.schemas.sla_schema import SLA_FIELDS

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def extract_sla_with_llm(text: str) -> dict:
    """
    Enhanced LLM-based SLA extractor for real-world lease contracts.
    More robust against complex formatting and multiple payment values.
    """

    # Start with full schema (safe default)
    sla_data = SLA_FIELDS.copy()

    if not GROQ_API_KEY:
        return sla_data

    # Limit contract size to avoid token overflow
    contract_text = text[:7000]

    prompt = f"""
You are an expert vehicle lease financial analyst.

Your task is to extract FINAL payable financial values from this lease contract.

Extraction Guidelines:

1. monthly_payment:
   - Extract the FINAL recurring monthly amount customer must pay.
   - Prefer values labeled "Total Monthly Payment" or "Monthly Payment Including Tax".
   - Do NOT extract base payment before taxes if total is available.

2. late_fees:
   - Extract the actual monetary late charge amount.
   - If percentage-based, return numeric percentage (e.g., 5%).
   - Ignore general policy text.

3. lease_term_months:
   - Extract total lease duration in months.

4. interest_rate:
   - Extract APR if available.
   - If only Money Factor exists, return it as-is.

5. down_payment:
   - Extract total upfront amount due at signing.

6. residual_value:
   - Extract end-of-term residual value.

7. buyout_price:
   - Extract purchase option price at lease end.

8. mileage_limit:
   - Extract total allowed miles (annual or total term).

Return ONLY valid JSON with exactly these keys:
interest_rate
lease_term_months
monthly_payment
down_payment
residual_value
mileage_limit
early_termination
late_fees
buyout_price

Rules:
- Remove currency symbols
- Return numeric values when possible
- If value not found, return null
- Do NOT explain anything
- Do NOT add extra keys

Contract:
{contract_text}
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You extract structured financial data from vehicle lease contracts."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)

        if response.status_code != 200:
            return sla_data

        content = response.json()["choices"][0]["message"]["content"]

        # 🔥 SAFE JSON EXTRACTION (handles extra text)
        json_match = re.search(r"\{.*\}", content, re.DOTALL)

        if not json_match:
            return sla_data

        extracted = json.loads(json_match.group())

        # Merge safely into schema
        for key in sla_data:
            if key in extracted:
                sla_data[key] = extracted[key]

        return sla_data

    except Exception:
        # Fail safely
        return sla_data
