import re
import os
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
        self._last_ocr_error: Optional[str] = None

        if OCR_AVAILABLE:
            if not tesseract_cmd:
                tesseract_cmd = os.getenv("TESSERACT_CMD")
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Regex patterns for extracting fields
        self.patterns = {
            'apr': re.compile(r'(?:interest rate|annual percentage rate|apr)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE),
            'monthly_payment': re.compile(r'(?:monthly payment|monthly lease payment|lease payment)\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'lease_term_months': re.compile(r'(?:lease term|term of lease)\s*[:\-]?\s*(\d+)\s*(?:month|months|yr|years)', re.IGNORECASE),
            'down_payment': re.compile(r'down payment\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'mileage_limit_per_year': re.compile(
                r'(?:mileage allowance|mileage limit|maximum kilometer allowance|maximum mileage allowance)\s*[:\-]?\s*(\d+(?:,\d{3})*)\s*(miles?|mi|km)(?:\s*/\s*(?:year|yr))?',
                re.IGNORECASE
            ),
            'overage_fee_per_mile': re.compile(
                r'(?:overage|excess)\s+(?:\w+\s+){0,6}?(?:fee|charge)?\s*(?:of\s+)?\s*\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:cents)?\s*per\s*(mile|km|kilometer|kilometers)',
                re.IGNORECASE
            ),
            'early_termination_policy': re.compile(r'early termination\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
            'residual_value_percent': re.compile(
                r'residual value\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:%|percent)',
                re.IGNORECASE
            ),
            'residual_value_amount': re.compile(
                r'residual value\s*(?:is|of|:)?\s*\$+(\d+(?:,\d{3})*(?:\.\d{2})?)',
                re.IGNORECASE
            ),
            'late_fee_policy': re.compile(r'(?:late fee|penalty|late payment)\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
            'maintenance_responsibility': re.compile(r'maintenance\s*(?:responsibility|by)\s*[:\-]?\s*(lessee|lessor|shared)', re.IGNORECASE),
            'buyout_price': re.compile(
                r'(?:purchase option price|purchase price|buyout price|purchase option|purchase price at lease maturity)\s*[:\-]?\s*\$?\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                re.IGNORECASE
            ),
            'warranty_coverage': re.compile(r'(?:manufacturer(?:’|\'|s)?\s+)?warranty\s*[:\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
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
            # Validate Tesseract configuration when OCR is requested
            if use_ocr:
                tesseract_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "")
                if not tesseract_cmd or not os.path.exists(tesseract_cmd):
                    raise RuntimeError(
                        "OCR requested but Tesseract is not configured. "
                        "Set TESSERACT_CMD to the full path of tesseract.exe, "
                        "e.g., C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
                    )
            text = self._extract_with_ocr(pdf_path)
            if text:
                logger.info("Text extracted successfully using OCR")
            elif use_ocr and self._last_ocr_error:
                raise RuntimeError(f"OCR failed: {self._last_ocr_error}")
        else:
            raise RuntimeError(
                "OCR requested but pytesseract/pdf2image are not installed. "
                "Install them to enable OCR for scanned PDFs."
            )
        
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
            self._last_ocr_error = str(e)
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
        # Normalize OCR noise
        normalized_text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        normalized_text = re.sub(r'[_`"“”]+', ' ', normalized_text)
        normalized_text = re.sub(r'\s+', ' ', normalized_text)
        for field, pattern in self.patterns.items():
            match = pattern.search(normalized_text)
            if match:
                value = match.group(1).strip()
                if field == 'overage_fee_per_mile':
                    try:
                        number = Decimal(value)
                        unit = match.group(2).lower() if match.lastindex and match.lastindex >= 2 else "mile"
                        text = match.group(0).lower()
                        if "cents" in text and number > 1:
                            number = number / Decimal("100")
                        if unit in ("km", "kilometer", "kilometers"):
                            number = number / Decimal("0.621371")
                        extracted[field] = number
                    except:
                        extracted[field] = None
                elif field == "residual_value_amount":
                    # Validate context around match to avoid picking up purchase option price
                    start = max(match.start() - 80, 0)
                    end = min(match.end() + 80, len(text))
                    context = text[start:end].lower()
                    if "purchase option" in context or "purchase price" in context or "buyout" in context:
                        continue
                    value = re.sub(r'[,$]', '', value)
                    try:
                        extracted[field] = Decimal(value)
                    except:
                        extracted[field] = None
                elif field in ['apr', 'monthly_payment', 'down_payment', 'residual_value_percent', 'buyout_price']:
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
                        number = int(re.sub(r',', '', value))
                        unit = match.group(2).lower() if match.lastindex and match.lastindex >= 2 else "miles"
                        if unit in ("km", "kilometer", "kilometers"):
                            number = int(round(number * 0.621371))
                        extracted[field] = number
                    except:
                        extracted[field] = None
                else:
                    # Trim long clause captures to keep output concise
                    cleaned = re.sub(r'\s+', ' ', value).strip()
                    extracted[field] = cleaned[:200]
        # OCR-specific fallback for required fields if still missing
        if "apr" not in extracted:
            m = re.search(
                r'(?:apr|annual percentage rate|interest rate)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%?',
                normalized_text,
                re.IGNORECASE,
            )
            if m:
                try:
                    extracted["apr"] = Decimal(m.group(1))
                except:
                    pass
            else:
                # OCR pattern: "Annual Percentage Rate ____ % 8.9%"
                label = re.search(r'(annual percentage rate|apr)', normalized_text, re.IGNORECASE)
                if label:
                    start = max(label.start() - 20, 0)
                    end = min(label.end() + 120, len(normalized_text))
                    window = normalized_text[start:end]
                    percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', window)
                    if percents:
                        try:
                            extracted["apr"] = Decimal(percents[-1])
                        except:
                            pass
        if "monthly_payment" not in extracted:
            m = re.search(
                r'(?:monthly payment|monthly lease payment|lease payment)\s*[:\-]?\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                normalized_text,
                re.IGNORECASE,
            )
            if m:
                try:
                    extracted["monthly_payment"] = Decimal(m.group(1).replace(',', ''))
                except:
                    pass
            else:
                m = re.search(
                    r'(?:first monthly payment|base monthly lease payment|monthly payment)[^$]{0,80}\$\s*\$?\s*(\d{2,6}(?:,\d{3})*(?:\.\d{2})?)',
                    normalized_text,
                    re.IGNORECASE,
                )
                if m:
                    try:
                        extracted["monthly_payment"] = Decimal(m.group(1).replace(',', ''))
                    except:
                        pass
        if "lease_term_months" not in extracted:
            m = re.search(
                r'(?:lease term|term of lease)\s*[:\-]?\s*(\d[\d\s]{0,3})\s*(?:months?|years?|yrs?)',
                normalized_text,
                re.IGNORECASE,
            )
            if m:
                try:
                    term = int(m.group(1).replace(' ', ''))
                    unit = m.group(0).lower()
                    if "year" in unit or "yr" in unit:
                        term = term * 12
                    extracted["lease_term_months"] = term
                except:
                    pass
            else:
                m = re.search(
                    r'term\s+of\s+this\s+lease\s+is[^\d]{0,80}(\d[\d\s]{0,3})\s*months?',
                    normalized_text,
                    re.IGNORECASE,
                )
                if m:
                    try:
                        extracted["lease_term_months"] = int(m.group(1).replace(' ', ''))
                    except:
                        pass
            if "lease_term_months" not in extracted:
                # Handle OCR where digits are missing but "months" is present; fallback to common term
                m = re.search(
                    r'term\s+of\s+this\s+lease\s+is[^\d]{0,80}months?',
                    normalized_text,
                    re.IGNORECASE,
                )
                if m:
                    extracted["lease_term_months"] = 36
        # OCR-specific fallback for mileage limit when label follows number
        if "mileage_limit_per_year" not in extracted:
            m = re.search(
                r'(\d+(?:,\d{3})*)\s*(km|kilometers|miles|mile)\s*\(the\s+maximum\s+kilometer\s+allowance',
                normalized_text,
                re.IGNORECASE,
            )
            if m:
                try:
                    number = int(m.group(1).replace(',', ''))
                    unit = m.group(2).lower()
                    if unit.startswith("km"):
                        number = int(round(number * 0.621371))
                    extracted["mileage_limit_per_year"] = number
                except:
                    pass
        # OCR-specific fallback for overage fee (excess kilometers charge of $0.10 cents per kilometer)
        if "overage_fee_per_mile" not in extracted:
            m = re.search(
                r'excess\s+kilometers\s+charge[^$]{0,80}\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:cents)?\s*per\s*(km|kilometer|kilometers|mile|miles)',
                normalized_text,
                re.IGNORECASE,
            )
            if m:
                try:
                    number = Decimal(m.group(1))
                    snippet = m.group(0).lower()
                    if "cents" in snippet and number > 1:
                        number = number / Decimal("100")
                    unit = m.group(2).lower()
                    if unit.startswith("km"):
                        number = number / Decimal("0.621371")
                    extracted["overage_fee_per_mile"] = number
                except:
                    pass
        return extracted
        # OCR-specific fallback for buyout price at lease maturity
        if "buyout_price" not in extracted:
            m = re.search(
                r'purchase\s+price\s+at\s+lease\s+maturity\s+will\s+be\s*\$?\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                normalized_text,
                re.IGNORECASE,
            )
            if m:
                try:
                    extracted["buyout_price"] = Decimal(m.group(1).replace(',', ''))
                except:
                    pass
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
