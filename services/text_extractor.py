import os
import re
import pytesseract
from pdf2image import convert_from_path
from typing import Optional
from PIL import Image

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF using OCR (Tesseract).
    This handles both digital PDFs and scanned images/photos of contracts.
    [cite: 108]
    """
    text = ""
    try:
        pages = convert_from_path(file_path, dpi=300)
        
        for i, page in enumerate(pages):
            page_text = pytesseract.image_to_string(page)
            
            text += f"--- Page {i+1} ---\n{page_text}\n"
            
        return text.strip()
    except Exception as e:
        raise Exception(f"OCR Extraction failed: {str(e)}")

def extract_vin_from_text(text: str) -> Optional[str]:
    """
    Extracts the 17-character Vehicle Identification Number (VIN) 
    from the OCR-processed text using regex patterns.
    [cite: 44, 45]
    """
    vin_patterns = [
        r'VIN[:\s]*([A-HJ-NPR-Z0-9]{17})',
        r'Vehicle\s*Identification\s*Number[:\s]*([A-HJ-NPR-Z0-9]{17})',
        r'\b([A-HJ-NPR-Z0-9]{17})\b' 
    ]
    
    for pattern in vin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None