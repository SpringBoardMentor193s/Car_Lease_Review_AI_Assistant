import pytesseract
from PIL import Image

# Point to the installed Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load a sample image (use an actual contract image here)
img = Image.open("samplelease.png")  # Replace with your image filename

# Extract text
text = pytesseract.image_to_string(img)
print("Extracted text:\n", text)