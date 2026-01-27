import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# If Tesseract is not in PATH, set it manually:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_from_image(image_path: str) -> str:
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

def ocr_from_pdf(pdf_path: str) -> str:
    pages = convert_from_path(pdf_path, poppler_path=r"C:\poppler-windows-25.12.0-0\bin")
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text