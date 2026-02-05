"""
LLM Service for AI-powered price negotiation and SLA extraction
Uses Groq API for fast inference
"""
import os
import json
from groq import Groq
from typing import Dict, Any, Optional


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        # Updated model - llama3-70b-8192 was decommissioned
        # Using llama-3.3-70b-versatile (newer, faster, better)
        self.model = "llama-3.3-70b-versatile"
    
    def negotiate_price(self, vehicle_data: Dict[str, Any], user_query: str = "") -> Dict[str, Any]:
        """
        Generate AI-powered price negotiation advice based on vehicle data from JSON storage
        
        Args:
            vehicle_data: Complete vehicle data including NHTSA info, recalls, and documents
            user_query: Optional user question about negotiation
        
        Returns:
            Structured negotiation recommendations
        """
        
        # Build context from JSON data
        context = self._build_negotiation_context(vehicle_data, user_query)
        
        # System prompt from PROMPTS_DESIGN.md
        system_prompt = """You are an expert automotive negotiation assistant helping users get the best deal on their car lease or purchase. You have access to comprehensive vehicle data including:

**Available Data:**
- VIN (Vehicle Identification Number)
- NHTSA vehicle specifications (year, make, model, trim, body class, engine, fuel type)
- Vehicle recalls and safety information
- Contract documents and OCR-extracted text
- Market comparisons and industry standards

**Your Role:**
1. Analyze the vehicle data and contract terms from JSON storage
2. Identify areas where the customer can negotiate better terms
3. Provide specific dollar amounts and percentage improvements
4. Suggest alternative terms based on market standards
5. Help the customer understand dealer markup, fees, and hidden costs
6. Recommend optimal negotiation strategies

**Negotiation Strategy:**
- Be professional but assertive
- Use data-driven arguments with specific numbers
- Reference industry standards and market rates
- Identify unnecessary fees and charges
- Suggest realistic counter-offers with justification
- Explain the reasoning behind each recommendation
- Consider recalls and vehicle condition in pricing

**Response Format:**
1. **Deal Summary**: Current terms at a glance
2. **Negotiation Opportunities**: Prioritized by potential savings
   - Current value vs. Recommended value
   - Savings amount and percentage
   - Justification and talking points
3. **Red Flags**: Unusual fees, excessive charges, unfavorable terms
4. **Recall Impact**: How any recalls affect negotiation leverage
5. **Action Plan**: Step-by-step negotiation approach
6. **Final Target**: Total savings potential

**Tone:** Professional, confident, and customer-focused. Act as the user's advocate.

**Important:** When analyzing recalls, consider:
- Safety issues = stronger negotiation position
- Recent recalls = demand price reduction or extended warranty
- Multiple recalls = significant leverage for better terms"""

        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            negotiation_advice = response.choices[0].message.content
            
            return {
                "status": "success",
                "vin": vehicle_data.get("vin"),
                "vehicle": self._extract_vehicle_summary(vehicle_data),
                "negotiation_advice": negotiation_advice,
                "has_recalls": len(vehicle_data.get("recalls", [])) > 0,
                "recall_count": len(vehicle_data.get("recalls", [])),
                "model_used": self.model
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "vin": vehicle_data.get("vin")
            }
    
    def extract_sla(self, vehicle_data: Dict[str, Any], contract_text: str) -> Dict[str, Any]:
        """
        Extract SLA parameters from contract using LLM
        Returns 11 required parameters plus fairness score
        
        Args:
            vehicle_data: Vehicle information from JSON storage
            contract_text: OCR-extracted contract text
        
        Returns:
            Dict with SLA parameters and fairness score (0-100)
        """
        
        # System prompt for SLA extraction (from PROMPTS_DESIGN.md)
        system_prompt = """You are an expert financial document analyst specializing in automotive lease and loan contracts. Your task is to extract Service Level Agreement (SLA) details from car lease/purchase contracts and provide a comprehensive fairness assessment.

**YOUR TASK:**
Extract the following REQUIRED SLA parameters with 100% accuracy. Do not estimate or guess values - use only what is explicitly stated in the document.

**REQUIRED SLA PARAMETERS TO EXTRACT:**

1. **Interest Rate / APR** - Annual Percentage Rate as percentage
2. **Lease Term Duration** - Contract duration in months
3. **Monthly Payment** - Base monthly payment amount
4. **Down Payment** - Total due at signing
5. **Residual Value** - Expected vehicle value at lease end (% of MSRP)
6. **Mileage Allowance & Overage Charges** - Annual limit and cost per excess mile
7. **Acquisition Fee** - Upfront processing fee
8. **Disposition Fee** - End-of-lease return fee
9. **Early Termination Penalties** - Cost to exit lease early
10. **Wear and Tear Standards** - Acceptable damage limits
11. **Purchase Option Price** - Buyout price at lease end

**FAIRNESS SCORE (0-100):**
Analyze the contract and assign a fairness score where:
- 90-100: Excellent deal, highly favorable to consumer
- 70-89: Good deal, competitive terms
- 50-69: Fair deal, industry standard
- 30-49: Below average, some unfavorable terms
- 0-29: Poor deal, heavily favors dealer

**Output Format:**
Return a JSON object with all 11 parameters and the fairness score with detailed justification."""

        context = f"""**Vehicle Information:**
VIN: {vehicle_data.get('vin')}
Make: {vehicle_data.get('vehicle_info', {}).get('Make', 'Unknown')}
Model: {vehicle_data.get('vehicle_info', {}).get('Model', 'Unknown')}
Year: {vehicle_data.get('vehicle_info', {}).get('ModelYear', 'Unknown')}

**Contract Text:**
{contract_text[:4000]}

Please extract all SLA parameters and calculate the Contract Fairness Score."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,  # Lower temperature for precise extraction
                max_tokens=2000
            )
            
            sla_data = response.choices[0].message.content
            
            return {
                "status": "success",
                "vin": vehicle_data.get("vin"),
                "sla_extraction": sla_data,
                "model_used": self.model
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "vin": vehicle_data.get("vin")
            }
    
    def _build_negotiation_context(self, vehicle_data: Dict[str, Any], user_query: str) -> str:
        """Build context string for negotiation LLM prompt"""
        
        vehicle_info = vehicle_data.get("vehicle_info", {})
        recalls = vehicle_data.get("recalls", [])
        documents = vehicle_data.get("documents", [])
        
        # Extract contract details if available
        contract_text = ""
        if documents:
            latest_doc = documents[0]
            contract_text = latest_doc.get("ocr_text", "")[:2000]  # Limit text size
        
        context = f"""**Vehicle Details:**
VIN: {vehicle_data.get('vin')}
Year: {vehicle_info.get('ModelYear', 'Unknown')}
Make: {vehicle_info.get('Make', 'Unknown')}
Model: {vehicle_info.get('Model', 'Unknown')}
Trim: {vehicle_info.get('Trim', 'Unknown')}
Body Class: {vehicle_info.get('BodyClass', 'Unknown')}
Engine: {vehicle_info.get('EngineConfiguration', 'Unknown')} - {vehicle_info.get('DisplacementL', 'Unknown')}L
Fuel Type: {vehicle_info.get('FuelTypePrimary', 'Unknown')}

**Recalls:** {len(recalls)} recall(s) found
"""
        
        if recalls:
            context += "\n**Recall Details:**\n"
            for i, recall in enumerate(recalls[:3], 1):  # Show first 3 recalls
                context += f"{i}. Component: {recall.get('Component', 'Unknown')}\n"
                context += f"   Summary: {recall.get('Summary', 'No summary')[:200]}\n"
        
        if contract_text:
            context += f"\n**Contract Information (OCR Extracted):**\n{contract_text}\n"
        
        if user_query:
            context += f"\n**User Question:** {user_query}\n"
        else:
            context += "\n**User Question:** Please analyze this vehicle and provide comprehensive negotiation advice.\n"
        
        return context
    
    def _extract_vehicle_summary(self, vehicle_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract clean vehicle summary for response"""
        vehicle_info = vehicle_data.get("vehicle_info", {})
        return {
            "vin": vehicle_data.get("vin"),
            "year": vehicle_info.get("ModelYear", "Unknown"),
            "make": vehicle_info.get("Make", "Unknown"),
            "model": vehicle_info.get("Model", "Unknown"),
            "trim": vehicle_info.get("Trim", "Unknown")
        }


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
