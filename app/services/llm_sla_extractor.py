import os
import json
from groq import Groq
from app.models.sla_schema import SLASummary

# Initialize Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL_NAME = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """
You are a legal contract analysis assistant.

Your task:
- Extract SLA details from car lease contracts.
- Normalize values into structured fields.
- Convert words into numbers when possible.
- Convert percentages into numeric values.
- Convert currency amounts into numbers (no symbols).
- If information is clearly present but phrased differently, still extract it.

Rules:
- Do NOT guess.
- If a value is genuinely missing, return null.
- Return ONLY valid JSON.
- Follow the exact JSON schema provided.
"""


USER_PROMPT = """
Extract the following SLA details from the car lease contract text below.

For each field:
- If the value is stated using words, convert it to a number.
- If currency symbols are present, remove them.
- If percentages are present, return numeric percentage values.
- If responsibility is mentioned (e.g., lessee/lessor), return exactly "Lessee" or "Lessor".

Fields to extract:
- interest_rate_apr
- lease_term_months
- monthly_payment
- down_payment
- residual_value
- purchase_option_price
- mileage_allowance_km_per_year
- mileage_overage_fee_per_km
- early_termination_clause
- maintenance_responsibility
- warranty_coverage
- insurance_requirement
- late_fee_penalties
- red_flags
- fairness_score

Return JSON EXACTLY in this format:

{
  "interest_rate_apr": null,
  "lease_term_months": null,
  "monthly_payment": null,
  "down_payment": null,
  "residual_value": null,
  "purchase_option_price": null,
  "mileage_allowance_km_per_year": null,
  "mileage_overage_fee_per_km": null,
  "early_termination_clause": null,
  "maintenance_responsibility": null,
  "warranty_coverage": null,
  "insurance_requirement": null,
  "late_fee_penalties": null,
  "red_flags": [],
  "fairness_score": null
}

Contract Text:
<<<
{contract_text}
>>>
"""


def extract_sla_llm_based(contract_text: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT + "\n\nContract Text:\n" + contract_text
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.2,
        max_tokens=800
    )

    raw_text = response.choices[0].message.content.strip()

    parsed = json.loads(raw_text)
    validated = SLASummary(**parsed)

    return validated.dict()
