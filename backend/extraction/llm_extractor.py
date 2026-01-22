import os
import json
import requests
from dotenv import load_dotenv
from backend.schemas.sla_schema import SLA_FIELDS

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def extract_sla_with_llm(text: str) -> dict:
    """
    Real LLM-based SLA extractor using Groq API
    """

    # Always start with full schema
    sla_data = SLA_FIELDS.copy()

    if not GROQ_API_KEY:
        # Fallback safety
        return sla_data

    # 🔥 PROMPT ENGINEERING (MENTOR GOLD PART)
    prompt = f"""
You are a financial contract analyst.

Extract the following SLA fields from this vehicle lease contract text.

Return ONLY valid JSON with these keys:
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
- If value not found, use null
- Do NOT add extra keys
- Do NOT explain anything

Contract text:
{text[:4000]}
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You extract structured data from contracts."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)

        if response.status_code != 200:
            return sla_data

        content = response.json()["choices"][0]["message"]["content"]

        # Parse JSON safely
        extracted = json.loads(content)

        # Merge into schema (only allowed fields)
        for key in sla_data:
            if key in extracted:
                sla_data[key] = extracted[key]

        return sla_data

    except Exception as e:
        # In case LLM fails, return empty schema (safe fallback)
        return sla_data
