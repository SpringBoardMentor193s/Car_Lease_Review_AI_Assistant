import re


def clean_money(value: str):
    if not value:
        return None
    return value.replace(",", "").strip()


def find_first(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            if match.lastindex:
                return clean_money(match.group(1))
    return None


def extract_sla_fields(text: str):
    data = {}

    # Normalize OCR spacing
    text = re.sub(r"\s+", " ", text)

    # ===============================
    # LEASE TERM
    # ===============================
    lease_patterns = [
        # OLD strict pattern
        r"Lease Term:\s*(\d+)\s*months",

        # NEW real contract patterns
        r"(?:term of this lease is)[^\d]{0,20}(\d{1,3})\s*months?",
        r"(?:lease term)[^\d]{0,20}(\d{1,3})\s*months?",
        r"(\d{1,3})\s*months?"
    ]
    data["lease_term_months"] = find_first(text, lease_patterns)

    # ===============================
    # MONTHLY PAYMENT
    # ===============================
    monthly_patterns = [
        # OLD
        r"Monthly Payment:\s*\$?([\d,]+\.?\d*)",

        # NEW
        r"(?:total monthly payment)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})",
        r"(?:monthly payment)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})"
    ]
    data["monthly_payment"] = find_first(text, monthly_patterns)

    # ===============================
    # INTEREST RATE
    # ===============================
    interest_patterns = [
        # OLD
        r"Interest Rate:\s*([\d\.]+)%",

        # NEW
        r"(?:interest rate)[^\d]{0,20}([\d\.]+)\s*%",
        r"(?:per annum)[^\d]{0,10}([\d\.]+)\s*%",
        r"(?:apr)[^\d]{0,20}([\d\.]+)\s*%"
    ]
    data["interest_rate"] = find_first(text, interest_patterns)

    # ===============================
    # DOWN PAYMENT
    # ===============================
    down_patterns = [
        # OLD
        r"Down Payment:\s*\$?([\d,]+\.?\d*)",

        # NEW
        r"(?:down payment)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})",
        r"(?:capitalized cost reduction)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})"
    ]
    data["down_payment"] = find_first(text, down_patterns)

    # ===============================
    # RESIDUAL VALUE
    # ===============================
    residual_patterns = [
        # OLD
        r"Residual Value:\s*\$?([\d,]+\.?\d*)",

        # NEW
        r"(?:residual value)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})",
        r"(?:end of term value)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})"
    ]
    data["residual_value"] = find_first(text, residual_patterns)

    # ===============================
    # BUYOUT PRICE
    # ===============================
    buyout_patterns = [
        # OLD
        r"Buyout Price.*?:\s*\$?([\d,]+\.?\d*)",

        # NEW
        r"(?:purchase option price)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})",
        r"(?:buyout price)[^\$]{0,40}\$?\s*([\d,]+\.\d{2})"
    ]
    data["buyout_price"] = find_first(text, buyout_patterns)

    # ===============================
    # MILEAGE LIMIT
    # ===============================

    mileage_patterns = [
        # Old strict format
        r"Mileage Limit:\s*([\d,]+\s*(?:miles|kilometers).*?/year)",

        # 12000 miles per year
        r"([\d,]+\s*(?:miles|kilometers)\s*(?:per|/)\s*year)",

        # in excess of 54,000 kilometers
        r"in excess of\s*(?:kilometers|miles)?\s*([\d,]+)",
        
        # kilometers 54,000
        r"kilometers\s*([\d,]+)",

        # 54,000 km
        r"([\d,]+\s*(?:km|kilometers|miles))"
    ]

    mileage_value = None

    for pattern in mileage_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.lastindex:
                mileage_value = match.group(1).strip()
                break

    data["mileage_limit"] = mileage_value

    # ===============================
    # EARLY TERMINATION
    # ===============================
    if re.search(r"Early Termination", text, re.IGNORECASE):
        data["early_termination"] = "Clause present"
    else:
        data["early_termination"] = None

    # ===============================
    # LATE FEES
    # ===============================

    late_patterns = [
        # OLD strict pattern (keeps full sentence)
        r"Late Fees:\s*([^\n]+)",

        # Percentage-based late fee
        r"(?:late fees?)[^\d]{0,40}([\d\.]+%\s*(?:per\s*(?:month|annum|year))?)",

        # Money-based late fee
        r"(?:late charge)[^\$]{0,100}\$?\s*([\d,]+\.\d{2})",
        r"(?:charge of)[^\$]{0,20}\$?\s*([\d,]+\.\d{2})\s*(?:for each|per)"
    ]

    late_value = None

    for pattern in late_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.lastindex:
                late_value = match.group(1).strip()
                break

    data["late_fees"] = late_value


    return data
