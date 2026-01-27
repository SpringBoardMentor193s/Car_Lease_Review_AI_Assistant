import re

import re

def extract_vin_or_reg_from_ocr(text: str) -> str:
    if not text:
        return None
    # Look for "VIN:" followed by 17+ characters (allowing OCR mistakes)
    match = re.search(r'VIN[:\s-]*([A-Z0-9]{17,18})', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def is_valid_vin(text: str) -> bool:
    """
    Check if the given text is a valid VIN (17 characters, alphanumeric, excluding I, O, Q).
    """
    vin_pattern = r'^[A-HJ-NPR-Z0-9]{17}$'
    return re.match(vin_pattern, text) is not None