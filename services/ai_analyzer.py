import google.generativeai as genai
import json
import os
from typing import Dict, Any
from models.schemas import AnalysisRequest, AnalysisResponse, LeaseSLA

class AIAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
    
    def analyze_contract(self, analysis_request: AnalysisRequest) -> AnalysisResponse:
        """Analyze lease contract using AI."""
        try:
            context = self._build_context(analysis_request)
            
            prompt = f"""
            Analyze this car lease contract and provide detailed insights.
            
            CONTEXT:
            {context}
            
            CONTRACT TEXT:
            {analysis_request.contract_text}
            
            TASKS:
            1. Extract lease terms: APR, lease term, monthly payment, down payment, residual value, mileage limit, early termination fee
            2. Identify red flags and potential issues
            3. Calculate fairness score (1-100) based on market standards
            4. Recommend specific changes to improve terms
            5. Provide market comparison for similar vehicles
            6. Assess risks (financial, legal, maintenance)
            
            Return response in this JSON format:
            {{
                "lease_terms": {{
                    "apr": "string",
                    "lease_term": "string",
                    "monthly_payment": "string",
                    "down_payment": "string",
                    "residual_value": "string",
                    "mileage_limit": "string",
                    "early_termination_fee": "string",
                    "red_flags": ["string"],
                    "fairness_score": integer
                }},
                "recommended_changes": ["string"],
                "market_comparison": {{
                    "avg_apr": "string",
                    "avg_monthly_payment": "string",
                    "market_range": "string",
                    "competitive_position": "string"
                }},
                "risk_assessment": {{
                    "financial_risk": "string",
                    "legal_risk": "string",
                    "maintenance_risk": "string",
                    "overall_risk_level": "string"
                }}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            analysis_result = self._parse_response(response.text)
            
            return AnalysisResponse(**analysis_result)
            
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")
    
    def _build_context(self, analysis_request: AnalysisRequest) -> str:
        """Build context string from vehicle details."""
        context_parts = []
        
        if analysis_request.vehicle_details:
            vd = analysis_request.vehicle_details
            context_parts.append("VEHICLE INFORMATION:")
            context_parts.append(f"- VIN: {vd.vin}")
            
            if vd.specifications:
                context_parts.append("Specifications:")
                for key, value in vd.specifications.items():
                    if key in ['Make', 'Model', 'ModelYear', 'BodyClass', 'FuelType', 'EngineHP']:
                        context_parts.append(f"  - {key}: {value}")
            
            if vd.recall_count > 0:
                context_parts.append(f"Recalls: {vd.recall_count} open recall(s)")
        
        return "\n".join(context_parts)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and handle JSON extraction."""
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Could not parse AI response as JSON")