import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-2.5-flash"


def negotiation_chat(
    sla_data: dict,
    price_estimate: dict,
    fairness_score: float,
    user_message: str
) -> str:
    """
    Uses Gemini LLM to provide negotiation advice
    based on extracted SLA data, market price, and fairness score.
    """

    prompt = f"""
You are an expert car finance negotiation assistant.

Extracted contract details (SLA):
{sla_data}

Estimated fair market price range:
{price_estimate}

Contract fairness score (0–100):
{fairness_score}

User question:
{user_message}

Instructions:
- Clearly state whether this deal is fair or overpriced
- Use APR, fees, and market price comparison
- Suggest specific negotiation points (APR reduction, fee removal, price adjustment)
- Be practical and concise
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()
