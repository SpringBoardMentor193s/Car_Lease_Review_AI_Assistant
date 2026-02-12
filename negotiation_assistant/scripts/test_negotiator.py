import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Load environment variables
load_dotenv(root_dir / ".env")
load_dotenv(root_dir / "negotiation_assistant" / ".env")

from negotiation_assistant.engine.negotiator import Negotiator
from negotiation_assistant.models.negotiation import NegotiationRequest, EmailGenerationRequest, NegotiationPoint

def test_integrated_negotiator():
    # Sample data that would come from extract/score endpoints
    contract_facts = {
        "apr": 8.5,
        "monthly_payment": 550,
        "lease_term_months": 36,
        "down_payment": 3000,
        "mileage_limit_per_year": 10000,
        "overage_fee_per_mile": 0.30,
        "residual_value_percent": 50,
        "maintenance_responsibility": "lessee"
    }
    
    fairness_report = {
        "overall_score": 45,
        "verdict": "Risky",
        "red_flags": [
            "High APR compared to market average (6.5%)",
            "High overage fee per mile",
            "Low annual mileage limit"
        ],
        "subscores": {
            "apr_fairness": 40,
            "mileage_fairness": 50,
            "cost_efficiency": 45
        }
    }
    
    market_data = {
        "apr": {"mean": 6.5},
        "overage_fee_per_mile": {"mean": 0.20},
        "mileage_limit_per_year": {"mean": 12000}
    }
    
    user_objectives = ["Lower the monthly payment", "Increase mileage limit to 12000"]
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable not set.")
        return

    negotiator = Negotiator()
    
    try:
        print("--- STEP 1: Generating Negotiation Strategy ---")
        request = NegotiationRequest(
            contract_facts=contract_facts,
            fairness_report=fairness_report,
            market_data=market_data,
            user_objectives=user_objectives
        )
        
        strategy = negotiator.generate_strategy(request)
        
        print("\n[Suggested Questions]")
        for q in strategy.suggested_questions:
            print(f"- {q}")
            
        print("\n[Contract-Specific Negotiation Points]")
        for p in strategy.contract_specific_points:
            print(f"Topic: {p.topic}")
            print(f"  Current: {p.current_value} -> Target: {p.target_value}")
            print(f"  Rationale: {p.rationale}")
            print()
            
        print("\n[General Negotiation Advice]")
        for p in strategy.general_points:
            print(f"Topic: {p.topic}")
            print(f"  Advice: {p.advice}")
            print(f"  Strategy: {p.strategy}")
            print()
            
        print("\n[Chat Template]")
        print(strategy.chat_template)

        print("\n--- STEP 2: Generating Email Template (Based on specific points) ---")
        # Simulate user selecting specific points to include in email
        selected_points = strategy.contract_specific_points[:2] 
        
        email_request = EmailGenerationRequest(
            contract_facts=contract_facts,
            negotiation_points=selected_points,
            user_tone="firm"
        )
        
        email = negotiator.generate_email(email_request)
        
        print(f"\nSubject: {email.subject}")
        print("-" * 20)
        print(email.body)
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integrated_negotiator()
