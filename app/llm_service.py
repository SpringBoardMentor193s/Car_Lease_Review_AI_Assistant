import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _extract_text_from_response(response):
    # Try common response access patterns used by OpenAI SDKs
    try:
        return response.choices[0].message.content
    except Exception:
        pass
    try:
        return response.choices[0].message['content']
    except Exception:
        pass
    try:
        return response.choices[0].text
    except Exception:
        pass
    # Fallback to string representation
    try:
        return str(response)
    except Exception:
        return ""


def _extract_json_from_text(text):
    if not text or not isinstance(text, str):
        raise ValueError("No text to parse JSON from")

    # Remove markdown fences
    text = re.sub(r"```(?:json)?\n?|```", "", text, flags=re.IGNORECASE)

    # Try extracting a JSON object with a simple regex first
    m = re.search(r"({[\s\S]*})", text)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # As a fallback, try to load the whole text
    try:
        return json.loads(text)
    except Exception as e:
        raise e


def extract_sla(contract_text):
    prompt = f"""
    Extract SLA details from the car lease/loan contract.
    Return ONLY valid JSON.

    Keys:
    interest_rate
    lease_term
    monthly_payment
    mileage_limit
    penalties
    early_termination

    Contract Text:
    {contract_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = _extract_text_from_response(response)

    try:
        return _extract_json_from_text(content)
    except Exception:
        return {
            "error": "LLM did not return valid JSON",
            "raw_response": content
        }
