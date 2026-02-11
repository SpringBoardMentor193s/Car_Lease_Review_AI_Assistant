from email.mime import text
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
    # BUYOUT PRICE / PURCHASE OPTION
    # ===============================

    buyout_value = None

    money_pattern = r"\$?\s*([\d,]+(?:\.\d{2})?)"

    # 1️⃣ Strict format with colon
    m = re.search(
        rf"(Buyout Price|Purchase Option Price)[^\n:]*:\s*{money_pattern}",
        text,
        re.IGNORECASE
    )
    if m:
        buyout_value = m.group(2 if m.lastindex > 1 else 1).replace(",", "")

    # 2️⃣ Buyout Price at End of Lease $XXXX
    if buyout_value is None:
        m = re.search(
            rf"Buyout Price[^$\n]*{money_pattern}",
            text,
            re.IGNORECASE
        )
        if m:
            buyout_value = m.group(1).replace(",", "")

    # 3️⃣ Real world clause
    if buyout_value is None:
        m = re.search(
            rf"purchase price at lease maturity.*?{money_pattern}",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if m:
            buyout_value = m.group(1).replace(",", "")

    # 4️⃣ $XXXX ... Purchase Option Price
    if buyout_value is None:
        m = re.search(
            rf"{money_pattern}.*?Purchase Option Price",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if m:
            buyout_value = m.group(1).replace(",", "")

    data["buyout_price"] = buyout_value




    # ===============================
    # MILEAGE LIMIT (With Units)
    # ===============================

    mileage_value = None

    # 1️⃣ Strict pattern (Mileage Limit: 12000 miles/year)
    limit_match = re.search(
        r"(?:Mileage Limit|Annual Mileage)[^\n:]*:\s*([\d,]+)\s*(miles\/year|km\/year|kilometers\/year)?",
        text,
        re.IGNORECASE
    )

    if limit_match:
        number = limit_match.group(1).replace(",", "")
        unit = limit_match.group(2)

        if unit:
            mileage_value = f"{number} {unit}"
        else:
            mileage_value = number


    # 2️⃣ Real-world pattern (in excess of 54,000 kilometers)
    if mileage_value is None:
        excess_match = re.search(
            r"in excess of\s*(?:kilometers|km|miles)?\s*([\d,]+)",
            text,
            re.IGNORECASE
        )

        if excess_match:
            number = excess_match.group(1).replace(",", "")
            mileage_value = f"{number} km"


    # 3️⃣ Generic fallback (avoid odometer)
    if mileage_value is None:
        for match in re.finditer(
            r"([\d,]+)\s*(km|kilometers|miles)",
            text,
            re.IGNORECASE
        ):
            context = text[max(0, match.start()-50):match.start()].lower()

            if "odometer" in context or "reading" in context:
                continue

            number = match.group(1).replace(",", "")
            unit = match.group(2)
            mileage_value = f"{number} {unit}"
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
