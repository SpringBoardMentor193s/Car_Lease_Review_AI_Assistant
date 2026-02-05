from __future__ import annotations

import re
from typing import Dict, Optional

import requests

VIN_REGEX = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")


def find_vin(text: str) -> Optional[str]:
    if not text:
        return None
    match = VIN_REGEX.search(text.upper())
    return match.group(1) if match else None


def decode_vin(vin: str) -> Dict[str, str]:
    vin = vin.strip().upper()
    if not vin:
        return {}
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    data = requests.get(url, timeout=15).json()
    result = data.get("Results", [{}])[0]
    cleaned = {}
    for key, value in result.items():
        value = str(value).strip()
        if value and value != "None":
            cleaned[key] = value
    return cleaned
