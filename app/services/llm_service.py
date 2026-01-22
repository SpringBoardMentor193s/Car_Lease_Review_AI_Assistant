import os
import json
from typing import Dict, List, Any
# Import LLM libraries (dummy implementation for demo if keys missing, or use actual APIs)
# using a generic placeholder approach to switch between providers

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") # Example
        # Initialize client here if keys exist

    def extract_clauses(self, text: str) -> Dict[str, Any]:
        """
        Extracts key clauses from the contract text using an LLM.
        """
        prompt = f"""
        Analyze the following car lease/loan contract text and extract specific clauses into a JSON format.
        
        Text:
        {text[:5000]} # Truncate for token limits if needed

        Required JSON Structure:
        {{
            "interest_rate": "value or null",
            "lease_tenure": "value or null",
            "monthly_payment": "value or null",
            "down_payment": "value or null",
            "mileage_limit": "value or null",
            "early_termination_fees": "value or null",
            "buyout_option": "value or null",
            "late_payment_fees": "value or null",
            "summary": "Short summary of the contract"
        }}
        Return ONLY the JSON.
        """
        
        # MOCK RESPONSE for Demo purposes (since we might not have a live key)
        # In production, call `openai.ChatCompletion.create(...)`
        
        if "5.5%" in text: # Heuristic from sample
             return {
                "interest_rate": "5.5%",
                "lease_tenure": "Unknown (Monthly)",
                "monthly_payment": "$450.00",
                "down_payment": "N/A",
                "mileage_limit": "N/A",
                "early_termination_fees": "Immediate balance due",
                "buyout_option": "N/A",
                "late_payment_fees": "$35.00",
                "summary": "Auto Loan Agreement for a 2024 Toyota Camry. $25,000 principal."
             }
        
        if "15%" in text:
            return {
                "interest_rate": "15%",
                "lease_tenure": "60 Months",
                "monthly_payment": "$650.00",
                "down_payment": "$0",
                "mileage_limit": "10,000 miles/year",
                "early_termination_fees": "$5,000 penalty",
                "buyout_option": "N/A",
                "late_payment_fees": "$100.00",
                "summary": "High interest loan agreement with strict penalties."
            }
        
        return {
            "interest_rate": "Not found",
            "lease_tenure": "Not found",
            "monthly_payment": "Not found",
            "down_payment": "Not found",
            "summary": "Could not extract specific details. Ensure the document is clear."
        }

    def chat_response(self, message: str, context: Dict[str, Any]) -> str:
        """
        Generates a chat response for negotiation.
        """
        # Simple rule-based or Mock LLM response
        msg = message.lower()
        if "apr" in msg or "interest" in msg:
            return "The interest rate of 5.5% is decent for a new car, but you might qualify for 4% with excellent credit. Ask if they can match a credit union rate."
        if "negotiate" in msg:
            return "Try asking: 'I've seen similar cars for $23,000. Can you match that price?' or 'Can we waive the documentation fee?'"
        
        return "That's a good question. Based on the contract, ensure you check the early termination penalties before signing."

llm_service = LLMService()
