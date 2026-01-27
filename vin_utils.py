# vin_utils.py
import re

def clean_vin(vin_raw: str) -> str:
    if not vin_raw:
        return None
    vin = vin_raw.strip().upper()
    vin = vin.replace("O", "0").replace("Q", "0").replace("I", "1")
    if len(vin) > 17:
        vin = vin[:17]
    return vin

def is_plausible_vin(vin: str) -> bool:
    # Basic plausibility: 17 chars, excludes I/O/Q
    return (
        isinstance(vin, str)
        and len(vin) == 17
        and not re.search(r"[IOQ]", vin)
    )