from pdf2image import convert_from_path
import pytesseract
from PIL import Image

POPPLER_PATH = r"C:\Users\vineelchandu\Downloads\poppler-25.12.0\Library\bin"

def extract_text(file_path):
    text = ""

    if file_path.lower().endswith(".pdf"):
        images = convert_from_path(
            file_path,
            poppler_path=POPPLER_PATH
        )
        for img in images:
            text += pytesseract.image_to_string(img)
    else:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)

    return text
