from typing import Dict, Any

def calculate_fairness_score(clauses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates a fairness score (0-100) based on extracted clauses.
    """
    score = 100
    explanation = []
    
    # 1. Interest Rate Check
    ir_str = clauses.get("interest_rate", "0").replace("%", "").strip()
    try:
        ir = float(ir_str)
        if ir > 10:
            score -= 20
            explanation.append("Interest rate is high (>10%).")
        elif ir > 7:
            score -= 10
            explanation.append("Interest rate is slightly above average.")
        else:
             explanation.append("Interest rate is competitive.")
    except:
        explanation.append("Could not parse interest rate.")

    # 2. Late Fees
    if clauses.get("late_payment_fees"):
         score -= 5
         explanation.append("Contract includes late payment fees.")

    # 3. Termination Fees
    term = clauses.get("early_termination_fees", "").lower()
    if "immediate" in term or "due" in term:
        score -= 10
        explanation.append("Strict early termination penalties detected.")

    return {
        "score": max(0, score),
        "explanation": " ".join(explanation)
    }
