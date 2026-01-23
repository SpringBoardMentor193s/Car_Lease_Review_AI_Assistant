import re
from decimal import Decimal
from typing import Dict, Any, Optional
import pdfplumber
from pathlib import Path

class PDFExtractor:
    def __init__(self):
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

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

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

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Main method to extract data from PDF."""
        text = self.extract_text_from_pdf(pdf_path)
        return self.extract_fields(text)