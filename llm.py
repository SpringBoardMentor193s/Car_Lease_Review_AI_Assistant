# app/llm.py
import os
import openai
from dotenv import load_dotenv

load_dotenv()  # <- load .env automatically

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_sla_features(contract_text: str) -> dict:
    """
    Call GPT to extract key SLA features from contract text.
    """
    prompt = f"""
    Extract the following key features from this lease/loan contract:

    - APR / Interest Rate
    - Lease Term
    - Monthly Payment
    - Down Payment
    - Residual Value
    - Mileage Allowance & Overage Charges
    - Early Termination Clause
    - Purchase Option / Buyout Price
    - Maintenance Responsibilities
    - Warranty & Insurance Coverage
    - Penalties or Late Fee Clauses

    Return as JSON with keys exactly as above. Contract text:
    {contract_text}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    text = response['choices'][0]['message']['content']
    
    try:
        import json
        return json.loads(text)
    except:
        return {"error": "Failed to parse GPT output", "raw_text": text}
