import os
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from negotiation_assistant.models.negotiation import (
    NegotiationRequest, 
    NegotiationResponse, 
    NegotiationPoint, 
    GeneralNegotiationPoint,
    EmailGenerationRequest,
    EmailTemplateResponse
)

# Load environment variables from .env if present
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logger = logging.getLogger(__name__)


def _json_safe_dumps(value: Any, indent: int = 2) -> str:
    return json.dumps(value, indent=indent, default=str)


# Guardrails to avoid suggestions that are directionally harmful for the customer.
LOWER_IS_BETTER_TOPICS = {
    "apr",
    "monthly payment",
    "down payment",
    "overage fee",
    "overage fee per mile",
    "buyout price",
}

HIGHER_IS_BETTER_TOPICS = {
    "mileage limit",
    "mileage limit per year",
}


def _topic_direction(topic: str) -> Optional[str]:
    t = (topic or "").strip().lower()
    for key in LOWER_IS_BETTER_TOPICS:
        if key in t:
            return "lower"
    for key in HIGHER_IS_BETTER_TOPICS:
        if key in t:
            return "higher"
    return None


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None

# Check for Groq availability
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed. Run: pip install groq")

SYSTEM_PROMPT = """You are an expert Car Lease Negotiation Assistant. 
Your goal is to help users get the best possible deal by analyzing their specific contract terms and providing general negotiation wisdom.

Based on the provided contract facts, fairness report, and market benchmarks, you must generate a JSON object with the following structure:

{
  "suggested_questions": ["Question 1", "Question 2"],
  "contract_specific_points": [
    {
      "topic": "Term Name (e.g., APR)",
      "current_value": "Current value from contract",
      "target_value": "Suggested target value",
      "rationale": "Why this needs negotiation",
      "leverage": "Arguments to use"
    }
  ],
  "general_points": [
    {
      "topic": "General Area (e.g., Doc Fees)",
      "advice": "General advice",
      "strategy": "How to negotiate"
    }
  ],
  "chat_template": "A brief message for the dealer"
}

Guidelines:
- Focus on terms that are significantly worse than market benchmarks or have red flags.
- For contract-specific points, ensure 'topic', 'current_value', 'target_value', 'rationale', and 'leverage' are ALWAYS provided.
- For general points, provide advice and strategy.
- Ensure the tone is professional but firm."""

EMAIL_SYSTEM_PROMPT = """You are an expert at drafting car lease negotiation emails.
Based on the contract facts and the specific negotiation points selected by the user, draft a professional and persuasive email to the car dealer.

The email should:
- Clearly state the points of negotiation.
- Use the provided rationale and leverage for each point.
- Maintain the requested tone (e.g., professional, firm, or friendly).
- Include a clear call to action.

Return a JSON object with 'subject' and 'body' fields."""

class Negotiator:
    """AI engine for generating negotiation strategies for car leases."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Negotiator.
        """
        if not GROQ_AVAILABLE:
            raise ImportError("Groq package not installed. Run: pip install groq")
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables.")
        
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = model

    def generate_strategy(self, request: NegotiationRequest) -> NegotiationResponse:
        """
        Generate a negotiation strategy based on contract data.
        """
        if not self.client:
            raise ValueError("Groq client not initialized. Provide an API key.")

        user_prompt = self._build_strategy_prompt(request)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2500
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            # Map to NegotiationResponse
            contract_specific_points = []
            for p in result_json.get("contract_specific_points", []):
                try:
                    contract_specific_points.append(NegotiationPoint(**p))
                except Exception as e:
                    logger.warning(f"Skipping invalid contract-specific point: {p}. Error: {e}")

            # Drop points with directionally harmful targets (e.g., higher APR target).
            contract_specific_points = self._filter_harmful_points(contract_specific_points)

            general_points = []
            for p in result_json.get("general_points", []):
                try:
                    general_points.append(GeneralNegotiationPoint(**p))
                except Exception as e:
                    logger.warning(f"Skipping invalid general point: {p}. Error: {e}")

            return NegotiationResponse(
                suggested_questions=result_json.get("suggested_questions", []),
                contract_specific_points=contract_specific_points,
                general_points=general_points,
                chat_template=result_json.get("chat_template", "")
            )
            
        except Exception as e:
            logger.error(f"Negotiation strategy generation failed: {e}")
            raise

    def generate_email(self, request: EmailGenerationRequest) -> EmailTemplateResponse:
        """
        Generate a custom negotiation email.
        """
        if not self.client:
            raise ValueError("Groq client not initialized. Provide an API key.")

        user_prompt = f"""Draft a {request.user_tone} negotiation email.
        
### Contract Facts:
{_json_safe_dumps(request.contract_facts, indent=2)}

### Selected Negotiation Points:
{_json_safe_dumps([p.dict() for p in request.negotiation_points], indent=2)}

Return JSON with 'subject' and 'body'."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EMAIL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            return EmailTemplateResponse(**result_json)
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            raise

    def _build_strategy_prompt(self, request: NegotiationRequest) -> str:
        """Construct the user prompt for strategy generation."""
        prompt_parts = ["Generate a comprehensive negotiation strategy:"]
        
        prompt_parts.append("\n### Extracted Contract Facts:")
        prompt_parts.append(_json_safe_dumps(request.contract_facts, indent=2))
        
        if request.fairness_report:
            prompt_parts.append("\n### Fairness Evaluation (Red Flags & Scores):")
            prompt_parts.append(_json_safe_dumps(request.fairness_report, indent=2))
            
        if request.market_data:
            prompt_parts.append("\n### Market Benchmarks for Comparison:")
            prompt_parts.append(_json_safe_dumps(request.market_data, indent=2))
            
        if request.user_objectives:
            prompt_parts.append("\n### User's Specific Goals:")
            for objective in request.user_objectives:
                prompt_parts.append(f"- {objective}")
                
        prompt_parts.append("\nReturn JSON with keys: suggested_questions (list), contract_specific_points (list), general_points (list), chat_template (string).")
        
        return "\n".join(prompt_parts)

    def _filter_harmful_points(self, points: List[NegotiationPoint]) -> List[NegotiationPoint]:
        safe_points: List[NegotiationPoint] = []
        for point in points:
            direction = _topic_direction(point.topic)
            if not direction:
                safe_points.append(point)
                continue

            current_val = _to_decimal(point.current_value)
            target_val = _to_decimal(point.target_value)
            if current_val is None or target_val is None:
                safe_points.append(point)
                continue

            is_harmful = (
                (direction == "lower" and target_val >= current_val)
                or (direction == "higher" and target_val <= current_val)
            )
            if is_harmful:
                logger.warning(
                    "Dropping harmful negotiation point: topic=%s current=%s target=%s",
                    point.topic,
                    point.current_value,
                    point.target_value,
                )
                continue

            safe_points.append(point)

        return safe_points
