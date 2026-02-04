import re
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
import pdfplumber
from pathlib import Path

# OCR imports
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize PDF extractor with optional Tesseract path.
        
        Args:
            tesseract_cmd: Path to tesseract executable (required on Windows)
                          e.g., r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        """
        if tesseract_cmd and OCR_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Regex patterns for extracting fields
        self.patterns = {
            'apr': re.compile(r'(?:interest rate|apr)\s*[:\-]?\s*(\d+(?:\.\d+)?)%?', re.IGNORECASE),
            'monthly_payment': re.compile(r'monthly payment\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'lease_term_months': re.compile(r'lease term\s*[:\-]?\s*(\d+)\s*(?:month|yr)', re.IGNORECASE),
            'down_payment': re.compile(r'down payment\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'mileage_limit_per_year': re.compile(r'mileage allowance\s*[:\-]?\s*(\d+(?:,\d{3})*)\s*(?:miles?|mi)', re.IGNORECASE),
            'overage_fee_per_mile': re.compile(r'overage(?:\s+fee)?\s*[:\-]?\s*\$?(\d+(?:\.\d{2})?)\s*per\s*mile', re.IGNORECASE),
            'early_termination_policy': re.compile(r'early termination\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
            'residual_value_percent': re.compile(r'residual value\s*[:\-]?\s*(\d+(?:\.\d+)?)%?', re.IGNORECASE),
            'late_fee_policy': re.compile(r'(?:late fee|penalty)\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
            'maintenance_responsibility': re.compile(r'maintenance\s*(?:responsibility|by)\s*[:\-]?\s*(lessee|lessor|shared)', re.IGNORECASE),
            'buyout_price': re.compile(r'(?:purchase option|buyout price)\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'warranty_coverage': re.compile(r'warranty\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
            'insurance_coverage': re.compile(r'insurance\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
        }

    def extract_text_from_pdf(self, pdf_path: str, use_ocr: bool = False) -> str:
        """
        Extract text from PDF using pdfplumber, with OCR fallback for scanned documents.
        
        Args:
            pdf_path: Path to the PDF file
            use_ocr: Force OCR extraction even if text is found
            
        Returns:
            Extracted text from the PDF
        """
        text = ""
        
        # First, try pdfplumber for digitally-created PDFs
        if not use_ocr:
            text = self._extract_with_pdfplumber(pdf_path)
            
            # Check if meaningful text was extracted
            if self._has_meaningful_text(text):
                logger.info("Text extracted successfully using pdfplumber")
                return text
            else:
                logger.info("No meaningful text found with pdfplumber, falling back to OCR")
        
        # Fallback to OCR for scanned/image-based PDFs
        if OCR_AVAILABLE:
            text = self._extract_with_ocr(pdf_path)
            if text:
                logger.info("Text extracted successfully using OCR")
        else:
            logger.warning("OCR not available. Install pytesseract and pdf2image for scanned PDF support.")
        
        return text
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
        return text
    
    def _extract_with_ocr(self, pdf_path: str, dpi: int = 300) -> str:
        """
        Extract text from PDF using OCR (Tesseract).
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for PDF to image conversion (higher = better quality but slower)
            
        Returns:
            Extracted text from OCR
        """
        if not OCR_AVAILABLE:
            return ""
        
        text = ""
        try:
            # Convert PDF pages to images
            logger.info(f"Converting PDF to images at {dpi} DPI...")
            images = convert_from_path(pdf_path, dpi=dpi)
            
            # Extract text from each page image
            for i, image in enumerate(images):
                logger.debug(f"Processing page {i + 1}/{len(images)} with OCR...")
                
                # Preprocess image for better OCR accuracy
                processed_image = self._preprocess_image_for_ocr(image)
                
                # Run OCR with optimized configuration
                page_text = pytesseract.image_to_string(
                    processed_image,
                    config='--oem 3 --psm 6'  # LSTM OCR engine, assume uniform block of text
                )
                
                if page_text:
                    text += page_text + "\n"
                    
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            
        return text
    
    def _preprocess_image_for_ocr(self, image: 'Image.Image') -> 'Image.Image':
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale for better OCR performance
        if image.mode != 'L':
            image = image.convert('L')
        
        return image
    
    def _has_meaningful_text(self, text: str, min_words: int = 10) -> bool:
        """
        Check if extracted text contains meaningful content.
        
        Args:
            text: Extracted text to evaluate
            min_words: Minimum word count to consider text meaningful
            
        Returns:
            True if text appears meaningful, False otherwise
        """
        if not text:
            return False
        
        # Count alphanumeric words
        words = re.findall(r'\b[a-zA-Z0-9]+\b', text)
        return len(words) >= min_words

    def extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract SLA parameters from text using regex patterns."""
        extracted = {}
        for field, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if field in ['apr', 'monthly_payment', 'down_payment', 'overage_fee_per_mile', 'residual_value_percent', 'buyout_price']:
                    # Clean numeric values
                    value = re.sub(r'[,$]', '', value)
                    try:
                        extracted[field] = Decimal(value)
                    except:
                        extracted[field] = None
                elif field == 'lease_term_months':
                    try:
                        extracted[field] = int(value)
                    except:
                        extracted[field] = None
                elif field == 'mileage_limit_per_year':
                    try:
                        extracted[field] = int(re.sub(r',', '', value))
                    except:
                        extracted[field] = None
                else:
                    extracted[field] = value
        return extracted

    def extract_from_pdf(self, pdf_path: str, use_ocr: bool = False) -> Dict[str, Any]:
        """
        Main method to extract data from PDF.
        
        Args:
            pdf_path: Path to the PDF file
            use_ocr: Force OCR extraction even if text is found
            
        Returns:
            Dictionary of extracted SLA parameters
        """
        text = self.extract_text_from_pdf(pdf_path, use_ocr=use_ocr)
        return self.extract_fields(text)
