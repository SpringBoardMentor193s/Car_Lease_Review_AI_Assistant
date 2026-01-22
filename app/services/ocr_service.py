import pytesseract
from PIL import Image
import io
import os

# Set Tesseract path if needed from env
# pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text from image or PDF files.
    For this demo, we assume images. For PDF, would need pdf2image.
    """
    try:
        # Simple check for image extension
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            return text
        elif filename.lower().endswith('.txt'):
            return file_bytes.decode('utf-8')
        elif filename.lower().endswith('.pdf'):
            # Placeholder for PDF implementation (requires pdf2image + poppler)
            return "[PDF Extraction skipped in this demo - requires poppler]. Please upload an image or text file."
        else:
            return "Unsupported file format."
    except Exception as e:
        print(f"Error in OCR: {e}")
        return ""
