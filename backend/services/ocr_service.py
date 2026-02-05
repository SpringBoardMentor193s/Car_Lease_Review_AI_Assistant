import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import os

# Configure Tesseract path for Windows (update if installed elsewhere)
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
]
TESSERACT_FOUND = False
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        TESSERACT_FOUND = True
        break

# Configure Poppler path for Windows
poppler_paths = [
    r'C:\poppler\poppler-24.08.0\Library\bin',
    r'C:\Program Files\poppler-24.08.0\Library\bin',
    r'C:\Program Files\poppler\Library\bin',
    r'C:\poppler\Library\bin',
]
POPPLER_PATH = None
for path in poppler_paths:
    if os.path.exists(path):
        POPPLER_PATH = path
        break

def extract_text(file_path):
    try:
        # Check if Tesseract is available
        if not TESSERACT_FOUND:
            return "⚠️ Tesseract OCR not installed. Please install from: https://github.com/UB-Mannheim/tesseract/wiki"
        
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            return "⚠️ Tesseract OCR not installed. Please install from: https://github.com/UB-Mannheim/tesseract/wiki"
        
        text = ""
        
        # Custom OCR configuration for better text extraction
        custom_config = r'--oem 3 --psm 6'
        
        if file_path.lower().endswith(".pdf"):
            # Convert PDF to images with higher DPI for better quality
            try:
                if POPPLER_PATH:
                    pages = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
                else:
                    pages = convert_from_path(file_path, dpi=300)
            except Exception as pdf_error:
                return f"⚠️ Poppler not found. Please install Poppler and add to PATH.\nDownload from: https://github.com/oschwartz10612/poppler-windows/releases\nError: {str(pdf_error)}"
            
            for i, page in enumerate(pages):
                page_text = pytesseract.image_to_string(page, config=custom_config)
                if page_text.strip():
                    text += f"\n--- Page {i+1} ---\n"
                    text += page_text + "\n"
        else:
            # For image files
            image = Image.open(file_path)
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image, config=custom_config)
        
        # Clean up and format as bullet points
        extracted_text = text.strip()
        if not extracted_text:
            return "No text extracted from document"
        
        # Convert to bullet points format
        lines = extracted_text.split('\n')
        bullet_points = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('---'):  # Skip empty lines and page markers
                # Add bullet point if not already present
                if not line.startswith('•') and not line.startswith('-') and not line.startswith('*'):
                    bullet_points.append(f"• {line}")
                else:
                    bullet_points.append(line)
            elif line.startswith('---'):  # Keep page markers
                bullet_points.append(line)
        
        return '\n'.join(bullet_points) if bullet_points else "No text extracted from document"
    except Exception as e:
        # Return detailed error info if OCR fails
        return f"OCR Error: {str(e)}"
