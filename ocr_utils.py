import re

def extract_vin_or_reg_from_ocr(text: str) -> str:
    # Clean OCR output
    cleaned = text.replace("-", "").upper()

    # VIN pattern (17 chars, no I/O/Q)
    vin_pattern = r'[A-HJ-NPR-Z0-9]{17}'
    match = re.search(vin_pattern, cleaned)
    return match.group(0) if match else None

def is_valid_vin(text: str) -> bool:
    """
    Check if the given text is a valid VIN (17 characters, alphanumeric, excluding I, O, Q).
    """
    vin_pattern = r'^[A-HJ-NPR-Z0-9]{17}$'
    return re.match(vin_pattern, text) is not None