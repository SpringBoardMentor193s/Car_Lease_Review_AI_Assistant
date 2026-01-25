import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY") 
)

MODEL_NAME = "gemini-2.5-flash"

def negotiation_chat(sla_data: dict, user_message: str) -> str:
    """
    Uses Gemini LLM to facilitate negotiation chat based on SLA data.
    Returns the LLM's response as a string.
    """

    prompt = f"""
You are an AI negotiation assistant for car lease and loan contracts.

Contract analysis:
{sla_data}

User question:
{user_message}

Instructions:
- Give clear, practical negotiation advice
- Explain risks if any
- Suggest what the user should ask the dealer
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()