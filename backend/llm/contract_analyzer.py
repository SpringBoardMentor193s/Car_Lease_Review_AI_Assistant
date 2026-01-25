import os
import json
from dotenv import load_dotenv
from google import genai
from backend.llm.schema import SLA_FIELDS

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Use a stable, supported Gemini model
MODEL_NAME = "gemini-2.5-flash"

def extract_sla(contract_text: str) -> dict:
    """
    Uses Gemini LLM to extract SLA fields from contract text.
    Returns a clean JSON dictionary.
    """

    prompt = f"""
You are a legal AI assistant specializing in car lease and loan contracts.

Extract the following SLA fields as a STRICT JSON object:
{SLA_FIELDS}

Rules:
- Return ONLY valid JSON
- Use null if a value is missing
- Do NOT include markdown
- Do NOT include explanations

Contract text:
{contract_text}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_output = response.text.strip()

        # 🔧 Remove markdown fences if Gemini adds them
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.strip().startswith("json"):
                raw_output = raw_output.replace("json", "", 1).strip()

        return json.loads(raw_output)

    except Exception as e:
        return {
            "error": "LLM SLA extraction failed",
            "details": str(e)
        }
