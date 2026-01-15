import re
from backend.schemas.sla_schema import SLA_FIELDS


def extract_sla_fields(text: str):
    # Start with full SLA schema
    data = SLA_FIELDS.copy()

    # Interest Rate / APR
    apr = re.search(r"\bAPR\b\s*[:\-]?\s*([\d.]+%)", text, re.IGNORECASE)
    if apr:
        data["interest_rate"] = apr.group(1)

    # Lease term (months)
    term = re.search(r"(\d{2,3})\s+months", text, re.IGNORECASE)
    if term:
        data["lease_term_months"] = term.group(1)

    # Monthly payment
    payment = re.search(
        r"\$\s?([\d,]+\.\d{2})\s+(per\s+month|monthly)",
        text,
        re.IGNORECASE
    )
    if payment:
        data["monthly_payment"] = payment.group(1)

    # Down payment
    down = re.search(
        r"(down payment|initial payment)\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if down:
        data["down_payment"] = down.group(2)

    # Residual value
    residual = re.search(
        r"residual value[^\$]*\$?\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if residual:
        data["residual_value"] = residual.group(1)

    # Mileage limit
    mileage = re.search(
        r"(\d{4,6})\s+(miles|kilometers)\s+per\s+year",
        text,
        re.IGNORECASE
    )
    if mileage:
        data["mileage_limit"] = mileage.group(1)

    # Late fees
    late = re.search(
        r"(late fee|late charge)[^\$]*\$?\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if late:
        data["late_fees"] = late.group(2)

    # Buyout / purchase option
    buyout = re.search(
        r"(purchase option|buyout)[^\$]*\$?\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if buyout:
        data["buyout_price"] = buyout.group(2)

    # Early termination clause (text-based)
    if "early termination" in text.lower():
        data["early_termination"] = "Clause present"

    return data
