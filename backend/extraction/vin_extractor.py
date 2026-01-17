import re

def extract_vin(text: str):
    """
    Extracts VIN from contract text using regex.
    VIN = 17 alphanumeric characters (excluding I, O, Q)
    """
    vin_pattern = r"\b[A-HJ-NPR-Z0-9]{17}\b"
    match = re.search(vin_pattern, text)

    return match.group(0) if match else None
