import pytesseract
from pdf2image import convert_from_path

# Explicit path to Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from scanned or image-based PDFs using Tesseract OCR.
    """
    images = convert_from_path(pdf_path)
    extracted_text = ""

    for img in images:
        text = pytesseract.image_to_string(img)
        extracted_text += text + "\n"

    return extracted_text.strip()
