import re

def extract_basic_fields(text):
    data = {}

    apr = re.search(r"APR\s*[:\-]?\s*([\d.]+%)", text, re.IGNORECASE)
    data["interest_rate"] = apr.group(1) if apr else None

    term = re.search(r"(\d{2,3})\s+months", text, re.IGNORECASE)
    data["lease_term_months"] = term.group(1) if term else None

    payment = re.search(r"\$\s?([\d,]+\.\d{2})\s+per\s+month", text, re.IGNORECASE)
    data["monthly_payment"] = payment.group(1) if payment else None

    return data
