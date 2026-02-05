"""
Contract comparison service
Compare multiple contracts side-by-side
"""
import os
import json
from typing import List, Dict


def compare_contracts(contract_ids: List[str]) -> Dict:
    """
    Compare multiple contracts side-by-side
    Returns structured comparison data
    """
    from pathlib import Path
    
    DATA_DIR = "vehicle_data"
    contracts = []
    
    # Gather contract data
    for contract_id in contract_ids[:3]:  # Limit to 3 contracts
        # Search for contract in all VIN files
        for json_file in Path(DATA_DIR).glob("*.json"):
            with open(json_file, "r") as f:
                data = json.load(f)
                for doc in data.get("documents", []):
                    doc_id = doc.get("contract_id") or doc.get("document_id")
                    if doc_id == contract_id:
                        contracts.append({
                            "contract_id": contract_id,
                            "vin": data.get("vin"),
                            "filename": doc.get("filename"),
                            "sla_data": doc.get("sla_data"),
                            "sla_extracted": doc.get("sla_extracted", False),
                            "vehicle_info": data.get("nhtsa_vehicle_info", {})
                        })
                        break
    
    if len(contracts) < 2:
        return {
            "status": "error",
            "message": "Need at least 2 contracts to compare"
        }
    
    # Build comparison
    comparison = {
        "status": "success",
        "contract_count": len(contracts),
        "contracts": contracts,
        "comparison": {
            "monthly_payments": [],
            "down_payments": [],
            "lease_terms": [],
            "total_costs": [],
            "fairness_scores": []
        },
        "recommendation": ""
    }
    
    # Extract comparable values
    for contract in contracts:
        sla = contract.get("sla_data", "")
        
        if isinstance(sla, str):
            # Parse if it's a string (extract numbers)
            import re
            
            # Monthly payment
            monthly_match = re.search(r'monthly.*?(\d{1,3}(?:,\d{3})*|\d+)', sla.lower())
            if monthly_match:
                monthly = monthly_match.group(1).replace(',', '')
                comparison["monthly_payments"].append({
                    "contract_id": contract["contract_id"],
                    "value": int(monthly)
                })
            
            # Down payment
            down_match = re.search(r'down.*?(\d{1,3}(?:,\d{3})*|\d+)', sla.lower())
            if down_match:
                down = down_match.group(1).replace(',', '')
                comparison["down_payments"].append({
                    "contract_id": contract["contract_id"],
                    "value": int(down)
                })
            
            # Lease term
            term_match = re.search(r'(?:term|duration).*?(\d+).*?month', sla.lower())
            if term_match:
                comparison["lease_terms"].append({
                    "contract_id": contract["contract_id"],
                    "value": int(term_match.group(1))
                })
            
            # Fairness score
            score_match = re.search(r'fairness.*?score.*?(\d+)', sla.lower())
            if score_match:
                comparison["fairness_scores"].append({
                    "contract_id": contract["contract_id"],
                    "value": int(score_match.group(1))
                })
    
    # Calculate total costs
    for i, contract in enumerate(contracts):
        monthly_payments = comparison["monthly_payments"]
        down_payments = comparison["down_payments"]
        lease_terms = comparison["lease_terms"]
        
        if (i < len(monthly_payments) and 
            i < len(down_payments) and 
            i < len(lease_terms)):
            
            monthly = monthly_payments[i]["value"]
            down = down_payments[i]["value"]
            term = lease_terms[i]["value"]
            
            total = (monthly * term) + down
            comparison["total_costs"].append({
                "contract_id": contract["contract_id"],
                "value": total
            })
    
    # Generate recommendation
    if comparison["total_costs"]:
        best_cost = min(comparison["total_costs"], key=lambda x: x["value"])
        comparison["recommendation"] = f"Contract {best_cost['contract_id'][:8]}... has the lowest total cost"
    
    if comparison["fairness_scores"]:
        best_score = max(comparison["fairness_scores"], key=lambda x: x["value"])
        comparison["recommendation"] += f" and Contract {best_score['contract_id'][:8]}... has the highest fairness score"
    
    return comparison


def get_contract_summary(contract_id: str) -> Dict:
    """Get summarized contract data for display"""
    from pathlib import Path
    
    DATA_DIR = "vehicle_data"
    
    for json_file in Path(DATA_DIR).glob("*.json"):
        with open(json_file, "r") as f:
            data = json.load(f)
            for doc in data.get("documents", []):
                doc_id = doc.get("contract_id") or doc.get("document_id")
                if doc_id == contract_id:
                    vehicle_info = data.get("nhtsa_vehicle_info", {})
                    
                    return {
                        "contract_id": contract_id,
                        "vin": data.get("vin"),
                        "filename": doc.get("filename"),
                        "vehicle": {
                            "make": vehicle_info.get("Make", "Unknown"),
                            "model": vehicle_info.get("Model", "Unknown"),
                            "year": vehicle_info.get("ModelYear", "Unknown"),
                        },
                        "sla_extracted": doc.get("sla_extracted", False),
                        "uploaded_at": doc.get("uploaded_at", "Unknown")
                    }
    
    return None
