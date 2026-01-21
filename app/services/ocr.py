import pytesseract
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path


def extract_text(file_path) -> str:
    """
    Extract text from PDF or image.
    Accepts both str and Path objects.
    """


    file_path = str(file_path)

    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
        if text.strip():
            return text
        return extract_text_from_pdf_ocr(file_path)

    else:
        return pytesseract.image_to_string(Image.open(file_path))


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def extract_text_from_pdf_ocr(file_path: str) -> str:
    images = convert_from_path(file_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text
