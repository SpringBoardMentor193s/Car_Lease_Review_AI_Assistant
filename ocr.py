from pdf2image import convert_from_path
import pytesseract
import os

# Make sure you have Poppler installed and provide the path
POPPLER_PATH = r"C:\Users\Neha\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

def extract_text(pdf_path: str) -> str:
    """
    Extract text from a PDF file using OCR (pdf2image + pytesseract).
    Args:
        pdf_path (str): Path to the PDF file.
    Returns:
        str: Extracted text from all pages.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    
    # Extract text from each page
    full_text = ""
    for i, page in enumerate(pages):
        text = pytesseract.image_to_string(page)
        full_text += text + "\n"
    
    return full_text
