import os
import pdfplumber
from typing import Optional

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def extract_vin_from_text(text: str) -> Optional[str]:
    """Extract VIN from contract text using pattern matching."""
    import re
    
    vin_patterns = [
        r'VIN[:\s]*([A-HJ-NPR-Z0-9]{17})',
        r'Vehicle\s*Identification\s*Number[:\s]*([A-HJ-NPR-Z0-9]{17})',
        r'([A-HJ-NPR-Z0-9]{17})' 
    ]
    
    for pattern in vin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None