from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class FieldExtraction:
    raw: Optional[str]
    value: Optional[float | int]


def clean_text(text: str) -> str:
    tmp = text.replace("\r", " ").replace("\n", " ")
    tmp = re.sub(r"\s+", " ", tmp)
    return tmp.strip()


def parse_amount(token: Optional[str]) -> Optional[float]:
    if not token:
        return None
    normalized = token.replace(",", "").replace(" ", "")
    normalized = normalized.replace("(", "-").replace(")", "")
    match = re.search(r"(-)?\$?([0-9]*\.?[0-9]+)([kK])?", normalized)
    if not match:
        return None
    sign, number, thousand = match.groups()
    value = float(number)
    if thousand:
        value *= 1000
    if sign:
        value *= -1
    return value


def parse_percentage(token: Optional[str]) -> Optional[float]:
    if not token:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", token)
    return float(match.group(1)) if match else None


def _find_first(patterns: Tuple[str, ...], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.lastindex:
                # pick last capturing group containing digits
                groups = [g for g in match.groups() if g]
                if groups:
                    return groups[-1]
            return match.group(0)
    return None


def extract_apr(text: str) -> FieldExtraction:
    patterns = (
        r"(?:APR|annual percentage rate|interest rate)[^\d%]{0,15}([0-9]+(?:\.[0-9]+)?\s*%)",
        r"interest rate[^\d]{0,15}([0-9]+(?:\.[0-9]+)?)\s*percent",
    )
    raw = _find_first(patterns, text)
    return FieldExtraction(raw=raw, value=parse_percentage(raw))


def extract_lease_term(text: str) -> FieldExtraction:
    patterns = (
        r"(?:lease term|term of lease|term)[:\s]{0,10}([0-9]{1,3}\s*(?:months|mos|yrs|years|year))",
        r"([0-9]{1,3}\s*(?:months|mos))",
        r"([0-9]{1,2})\s*(?:years|yrs)",
    )
    raw = _find_first(patterns, text)
    if not raw:
        return FieldExtraction(None, None)
    months = re.search(r"([0-9]{1,3})\s*(months|mos)", raw, re.IGNORECASE)
    if months:
        return FieldExtraction(raw, int(months.group(1)))
    years = re.search(r"([0-9]{1,2})\s*(years|yrs|year)", raw, re.IGNORECASE)
    if years:
        return FieldExtraction(raw, int(years.group(1)) * 12)
    digits = re.search(r"([0-9]{1,3})", raw)
    return FieldExtraction(raw, int(digits.group(1))) if digits else FieldExtraction(raw, None)


def extract_monthly_payment(text: str) -> FieldExtraction:
    patterns = (
        r"(?:monthly payment|monthly instalment|monthly installment|monthly lease payment)[^\d\$]{0,20}(\$?[0-9,]+(?:\.[0-9]+)?\s*[kK]?)",
        r"(?:payment of|installment of|installment)[^\d\$]{0,20}(\$?[0-9,]+(?:\.[0-9]+)?\s*[kK]?)(?:\s*(?:per month|/month|monthly))?",
        r"(\$[0-9,]+(?:\.[0-9]+)?\s*(?:per month|/month|monthly))",
    )
    raw = _find_first(patterns, text)
    return FieldExtraction(raw, parse_amount(raw))


def extract_down_payment(text: str) -> FieldExtraction:
    patterns = (
        r"down payment[^\d\$]{0,20}(\$?[0-9,]+(?:\.[0-9]+)?\s*[kK]?)",
        r"deposit[^\d\$]{0,20}(\$?[0-9,]+(?:\.[0-9]+)?\s*[kK]?)",
    )
    raw = _find_first(patterns, text)
    return FieldExtraction(raw, parse_amount(raw))


def extract_residual_value(text: str) -> FieldExtraction:
    patterns = (
        r"(?:residual value|residual)[^\d\$]{0,20}(\$?[0-9,]+(?:\.[0-9]+)?\s*[kK]?)",
        r"residual amount[^\d\$]{0,20}(\$?[0-9,]+)",
    )
    raw = _find_first(patterns, text)
    return FieldExtraction(raw, parse_amount(raw))


def extract_mileage_allowance(text: str) -> FieldExtraction:
    patterns = (
        r"(\d{1,3}(?:,[0-9]{3})?|\d{1,2}k)\s*(?:miles per year|miles/year|mi/year|miles per annum|miles p[er]{0,2} year)",
        r"mileage allowance[^\d]{0,20}(\d{1,3}(?:,[0-9]{3})?|\d{1,2}k)",
    )
    raw = _find_first(patterns, text)
    if not raw:
        return FieldExtraction(None, None)
    cleaned = raw.lower().replace(",", "").strip()
    multiplier = 1000 if cleaned.endswith("k") else 1
    if multiplier == 1000:
        cleaned = cleaned[:-1]
    try:
        value = int(float(cleaned)) * multiplier
    except ValueError:
        value = None
    return FieldExtraction(raw, value)


def extract_overage_fee(text: str) -> FieldExtraction:
    patterns = (
        r"(\$[0-9]+(?:\.[0-9]+)?)\s*(?:per mile|/mile|per mi)",
        r"(?:overage|excess mileage|excess miles)[^\d\$]{0,20}(\$?[0-9]+(?:\.[0-9]+)?)",
    )
    raw = _find_first(patterns, text)
    return FieldExtraction(raw, parse_amount(raw))


def extract_buyout_price(text: str) -> FieldExtraction:
    patterns = (
        r"(?:buyout|purchase option|purchase price|purchase option price)[^\d\$]{0,30}(\$?[0-9,]+(?:\.[0-9]+)?\s*[kK]?)",
        r"payoff amount[^\d\$]{0,30}(\$?[0-9,]+)",
    )
    raw = _find_first(patterns, text)
    return FieldExtraction(raw, parse_amount(raw))


CLAUSE_KEYWORDS = {
    "early_termination": ("early termination", "terminate"),
    "maintenance": ("maintenance", "service"),
    "warranty": ("warranty", "guarantee"),
    "insurance": ("insurance", "insured", "insurer"),
    "penalties": ("penalty", "late fee", "default"),
}


def extract_clause_snippet(text: str, keywords: Tuple[str, ...], window: int = 280) -> Optional[str]:
    lower_text = text.lower()
    for keyword in keywords:
        idx = lower_text.find(keyword.lower())
        if idx != -1:
            start = max(0, idx - 60)
            end = min(len(text), idx + window)
            return text[start:end].strip()
    return None


def extract_all(text: str) -> Dict[str, Optional[str | float | int | Dict[str, Optional[str]]]]:
    cleaned = clean_text(text)
    apr = extract_apr(cleaned)
    term = extract_lease_term(cleaned)
    monthly = extract_monthly_payment(cleaned)
    down = extract_down_payment(cleaned)
    residual = extract_residual_value(cleaned)
    mileage = extract_mileage_allowance(cleaned)
    overage = extract_overage_fee(cleaned)
    buyout = extract_buyout_price(cleaned)

    result: Dict[str, Optional[str | float | int | Dict[str, Optional[str]]]] = {
        "apr_raw": apr.raw,
        "apr_percent": apr.value,
        "lease_term_raw": term.raw,
        "lease_term_months": term.value,
        "monthly_payment_raw": monthly.raw,
        "monthly_payment": monthly.value,
        "down_payment_raw": down.raw,
        "down_payment": down.value,
        "residual_value_raw": residual.raw,
        "residual_value": residual.value,
        "mileage_raw": mileage.raw,
        "mileage_per_year": mileage.value,
        "overage_raw": overage.raw,
        "overage_per_mile": overage.value,
        "buyout_raw": buyout.raw,
        "buyout_price": buyout.value,
        "clauses": {},
    }

    clauses: Dict[str, Optional[str]] = {}
    for key, terms in CLAUSE_KEYWORDS.items():
        clauses[key] = extract_clause_snippet(text, terms)
    result["clauses"] = clauses
    return result
