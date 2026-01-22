import re


def extract_sla_fields(text: str):
    data = {}

    # Lease Term
    m = re.search(r"Lease Term:\s*(\d+)\s*months", text, re.IGNORECASE)
    data["lease_term_months"] = m.group(1) if m else None

    # Monthly Payment
    m = re.search(r"Monthly Payment:\s*\$?([\d,]+\.?\d*)", text, re.IGNORECASE)
    data["monthly_payment"] = m.group(1) if m else None

    # Interest Rate
    m = re.search(r"Interest Rate:\s*([\d\.]+)%", text, re.IGNORECASE)
    data["interest_rate"] = m.group(1) if m else None

    # Down Payment
    m = re.search(r"Down Payment:\s*\$?([\d,]+\.?\d*)", text, re.IGNORECASE)
    data["down_payment"] = m.group(1) if m else None

    # Residual Value
    m = re.search(r"Residual Value:\s*\$?([\d,]+\.?\d*)", text, re.IGNORECASE)
    data["residual_value"] = m.group(1) if m else None

    # Buyout Price
    m = re.search(r"Buyout Price.*?:\s*\$?([\d,]+\.?\d*)", text, re.IGNORECASE)
    data["buyout_price"] = m.group(1) if m else None

    # Mileage Limit
    m = re.search(r"Mileage Limit:\s*([\d,]+.*?/year)", text, re.IGNORECASE)
    data["mileage_limit"] = m.group(1) if m else None

    # Early Termination
    if re.search(r"Early Termination", text, re.IGNORECASE):
        data["early_termination"] = "Clause present"
    else:
        data["early_termination"] = None

    # Late Fees
    m = re.search(r"Late Fees:\s*([^\n]+)", text, re.IGNORECASE)
    data["late_fees"] = m.group(1).strip() if m else None

    return data
