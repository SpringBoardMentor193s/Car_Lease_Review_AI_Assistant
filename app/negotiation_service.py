import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _extract_text_from_response(response):
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
    try:
        return str(response)
    except Exception:
        return ""


def generate_negotiation_advice(sla_json):
    prompt = f"""
    You are an expert car lease negotiation assistant.

    Based on the SLA details below, provide:
    - Key negotiation points
    - What the customer should ask the dealer
    - Any risk warnings

    SLA Details:
    {sla_json}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = _extract_text_from_response(response)
    # strip markdown fences if present
    content = re.sub(r"```(?:[\s\S]*?)```", "", content)
    return content
