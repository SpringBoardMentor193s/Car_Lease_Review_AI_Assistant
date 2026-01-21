import re
from app.models.sla_schema import SLASummary


def extract_sla_rule_based(text: str) -> SLASummary:
    """
    Milestone 2
    Phase 2: Rule-based SLA extraction
    Phase 3: Fairness score + red flags
    """

    sla = SLASummary()

    # -------------------------
    # 1. Normalize text
    # -------------------------
    text = text.replace("\n", " ")
    text = " ".join(text.split())

    # -------------------------
    # 2. Interest Rate (APR)
    # -------------------------
    apr_match = re.search(
        r"Interest Rate\s*\(APR\)\s*[:\-]?\s*([\d.]+)",
        text,
        re.IGNORECASE,
    )
    sla.interest_rate_apr = float(apr_match.group(1)) if apr_match else None

    # -------------------------
    # 3. Lease Term (months)
    # -------------------------
    lease_term_match = re.search(
        r"(\d+)\s*months",
        text,
        re.IGNORECASE,
    )
    sla.lease_term_months = int(lease_term_match.group(1)) if lease_term_match else None

    # -------------------------
    # 4. Monthly Payment
    # -------------------------
    monthly_payment_match = re.search(
        r"Monthly.*?Payment.*?₹?\$?([\d,]+)",
        text,
        re.IGNORECASE,
    )
    sla.monthly_payment = (
        int(monthly_payment_match.group(1).replace(",", ""))
        if monthly_payment_match
        else None
    )

    # -------------------------
    # 5. Down Payment
    # -------------------------
    down_payment_match = re.search(
        r"Down.*?Payment.*?₹?\$?([\d,]+)",
        text,
        re.IGNORECASE,
    )
    sla.down_payment = (
        int(down_payment_match.group(1).replace(",", ""))
        if down_payment_match
        else None
    )

    # -------------------------
    # 6. Residual Value
    # -------------------------
    residual_value_match = re.search(
        r"Residual Value.*?₹?\$?([\d,]+)",
        text,
        re.IGNORECASE,
    )
    sla.residual_value = (
        int(residual_value_match.group(1).replace(",", ""))
        if residual_value_match
        else None
    )

    # -------------------------
    # 7. Purchase Option / Buyout
    # -------------------------
    purchase_option_match = re.search(
        r"(Purchase Option|Buyout Price).*?₹?\$?([\d,]+)",
        text,
        re.IGNORECASE,
    )
    sla.purchase_option_price = (
        int(purchase_option_match.group(2).replace(",", ""))
        if purchase_option_match
        else None
    )

    # -------------------------
    # 8. Mileage Allowance
    # -------------------------
    mileage_match = re.search(
        r"([\d,]+)\s*km\s*(per year|annually)",
        text,
        re.IGNORECASE,
    )
    sla.mileage_allowance_km_per_year = (
        int(mileage_match.group(1).replace(",", ""))
        if mileage_match
        else None
    )

    # -------------------------
    # 9. Mileage Overage Fee
    # -------------------------
    mileage_fee_match = re.search(
        r"([\d]+)\s*per\s*km",
        text,
        re.IGNORECASE,
    )
    sla.mileage_overage_fee_per_km = (
        int(mileage_fee_match.group(1)) if mileage_fee_match else None
    )

    # -------------------------
    # 10. Clause Extractor Helper
    # -------------------------
    def extract_clause(keyword: str, window: int = 300):
        idx = text.lower().find(keyword.lower())
        if idx != -1:
            return text[idx : idx + window].strip()
        return None

    sla.early_termination_clause = extract_clause("early termination")
    sla.maintenance_responsibility = extract_clause("maintenance")
    sla.warranty_coverage = extract_clause("warranty")
    sla.insurance_requirement = extract_clause("insurance")
    sla.late_fee_penalties = extract_clause("late payment")

    # =====================================================
    # PHASE 3 – FAIRNESS SCORE & RED FLAGS
    # =====================================================

    fairness_score = 100
    red_flags = []

    # -------------------------
    # Interest Rate Rules
    # -------------------------
    if sla.interest_rate_apr:
        if sla.interest_rate_apr > 12:
            fairness_score -= 15
            red_flags.append("High interest rate")
        elif sla.interest_rate_apr > 8:
            fairness_score -= 5

    # -------------------------
    # Mileage Overage Fee Rules
    # -------------------------
    if sla.mileage_overage_fee_per_km:
        if sla.mileage_overage_fee_per_km > 15:
            fairness_score -= 10
            red_flags.append("High mileage overage fee")
        elif sla.mileage_overage_fee_per_km > 10:
            fairness_score -= 5

    # -------------------------
    # Early Termination Rules
    # -------------------------
    if sla.early_termination_clause:
        clause_text = sla.early_termination_clause.lower()
        if "3 months" in clause_text or "three months" in clause_text:
            fairness_score -= 15
            red_flags.append("Severe early termination penalty")
        elif "1 month" in clause_text:
            fairness_score -= 5

    # -------------------------
    # Down Payment Rules
    # -------------------------
    if sla.down_payment and sla.residual_value:
        if sla.down_payment > 0.3 * sla.residual_value:
            fairness_score -= 10
            red_flags.append("High upfront down payment")

    # -------------------------
    # Late Fee Rules
    # -------------------------
    if sla.late_fee_penalties:
        if "1500" in sla.late_fee_penalties or "1000" in sla.late_fee_penalties:
            fairness_score -= 5
            red_flags.append("High late payment penalty")

    # -------------------------
    # Final Assignments
    # -------------------------
    sla.red_flags = red_flags
    sla.fairness_score = max(0, fairness_score)

    return sla
