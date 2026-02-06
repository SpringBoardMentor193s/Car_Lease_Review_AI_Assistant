"""
Extract Pipeline for Car Lease Review AI Assistant

This module handles the extraction of SLA parameters from uploaded PDF documents,
validates the data against the contract facts schema, and stores the results in the database.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import re
from models.contract_facts import ContractFacts
from engine.pdf_extractor import PDFExtractor
from database.db import ContractFactsDB

# Optional LLM extractor for complex documents
try:
    from engine.llm_extractor import LLMExtractor, HybridExtractor
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExtractPipeline:
    def __init__(self, db_path: str = "contract_facts.db", tesseract_cmd: Optional[str] = None, 
                 openai_api_key: Optional[str] = None):
        """
        Initialize the extraction pipeline.
        
        Args:
            db_path: Path to the SQLite database
            tesseract_cmd: Path to tesseract executable (required on Windows for OCR)
                          e.g., r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            openai_api_key: OpenAI API key for LLM-based extraction (optional)
        """
        self.extractor = PDFExtractor(tesseract_cmd=tesseract_cmd)
        self.db = ContractFactsDB(db_path)
        self.groq_api_key = openai_api_key  # Now using Groq instead of OpenAI
        
        # Initialize LLM extractor if available (using free Groq API)
        self.llm_extractor = None
        if LLM_AVAILABLE and openai_api_key:
            try:
                self.llm_extractor = LLMExtractor(api_key=openai_api_key)
                logger.info("LLM extractor initialized (Groq/Llama 3)")
            except Exception as e:
                logger.warning(f"Could not initialize LLM extractor: {e}")

    def run(self, pdf_path: str, use_ocr: bool = False, use_llm: bool = False) -> Optional[int]:
        """
        Run the extraction pipeline on a PDF file.

        Args:
            pdf_path: Path to the PDF file to process
            use_ocr: Force OCR extraction even if text is found (useful for scanned PDFs)
            use_llm: Use LLM for extraction (recommended for real/complex contracts)

        Returns:
            The database ID of the inserted record, or None if extraction/validation failed
        """
        try:
            logger.info(f"Starting extraction for PDF: {pdf_path}")
            
            # First extract text from PDF
            text = self.extractor.extract_text_from_pdf(pdf_path, use_ocr=use_ocr)
            
            if use_ocr and not text:
                raise RuntimeError(
                    "OCR produced no text. Verify Tesseract installation, "
                    "TESSERACT_CMD, and Poppler (pdf2image)."
                )

            # Choose extraction method
            if use_llm and self.llm_extractor:
                logger.info("Using LLM extraction for complex document")
                extracted_data = self.llm_extractor.extract_fields(text)
            else:
                # Use regex-based extraction
                extracted_data = self.extractor.extract_fields(text)

            extracted_data = self._override_from_text(text, extracted_data)
            extracted_data = self._normalize_clause_misclassification(extracted_data)
            extracted_data = self._normalize_mileage_total_to_annual(extracted_data)
            extracted_data = self._drop_residual_if_equals_buyout(extracted_data)
            logger.info(f"Extracted data: {extracted_data}")

            # Validate and create ContractFacts object
            contract_facts = self._validate_and_create_contract_facts(extracted_data)
            if not contract_facts:
                logger.error("Failed to validate extracted data")
                return None

            # Store in database
            record_id = self.db.insert_contract_facts(contract_facts)
            logger.info(f"Stored contract facts with ID: {record_id}")

            return record_id

        except RuntimeError as e:
            logger.error(f"Extraction runtime error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in extraction pipeline: {e}")
            return None

    def _normalize_clause_misclassification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect mileage-overage language mistakenly extracted as early termination.
        If found, map to overage_fee_per_mile and mileage_limit_per_year where possible.
        """
        early = data.get("early_termination_policy")
        if not early or not isinstance(early, str):
            return data

        text = re.sub(r"\s+", " ", early).strip().lower()
        if not re.search(r"per\s*(?:mile|km)|over\s+\d{4,6}\s*(?:miles|km)", text):
            return data

        # Try to extract fee per mile/km (e.g., $0.10 per km)
        fee_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*per\s*(mile|km)", text)
        if fee_match and data.get("overage_fee_per_mile") is None:
            fee = float(fee_match.group(1))
            unit = fee_match.group(2)
            if unit == "km":
                # Convert per-km fee to per-mile fee
                fee = fee / 0.621371
            data["overage_fee_per_mile"] = round(fee, 4)

        # Try to extract mileage limit (e.g., over 54,000 km)
        limit_match = re.search(r"over\s+(\d{4,6}(?:,\d{3})?)\s*(miles|km)", text)
        if limit_match and data.get("mileage_limit_per_year") is None:
            limit = int(limit_match.group(1).replace(",", ""))
            unit = limit_match.group(2)
            if unit == "km":
                limit = int(round(limit * 0.621371))

            # If lease term exists, interpret limit as total and normalize to annual
            term = data.get("lease_term_months")
            if term:
                years = float(term) / 12.0
                if years > 0:
                    limit = int(round(limit / years))
            data["mileage_limit_per_year"] = limit

        # Clear early termination policy if it looks like mileage overage
        data["early_termination_policy"] = None
        return data

    def _normalize_mileage_total_to_annual(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        If mileage limit looks like a total (very large), normalize to annual using lease term.
        """
        limit = data.get("mileage_limit_per_year")
        term = data.get("lease_term_months")
        if limit and term:
            try:
                limit_val = int(limit)
                years = float(term) / 12.0
                if years > 0 and limit_val > 20000:
                    data["mileage_limit_per_year"] = int(round(limit_val / years))
            except Exception:
                pass
        return data

    def _override_from_text(self, text: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse critical fields directly from raw text when phrasing is specific.
        This helps correct LLM/regex mis-assignments.
        """
        normalized = re.sub(r"\s+", " ", text).lower()

        # Residual value amount: only accept if explicitly labeled as residual value
        residual_match = re.search(
            r"residual value\s*(?:is|of|:)?\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
            normalized,
        )
        if residual_match:
            try:
                amount = float(residual_match.group(1).replace(",", ""))
                data["residual_value_amount"] = amount
            except Exception:
                pass
        else:
            data["residual_value_amount"] = None

        # Overage fee per km/mile (supports "cents per kilometer")
        overage_match = re.search(
            r"(?:excess|overage)\s+(?:[\w\W]{0,300}?)(?:charge|fee)?\s*(?:of\s+)?"
            r"\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:cents)?\s*per\s*(km|kilometer|kilometers|mile|miles)\b",
            normalized,
        )
        if overage_match:
            try:
                fee = float(overage_match.group(1))
                if "cents" in overage_match.group(0) and fee > 1:
                    fee = fee / 100.0
                unit = overage_match.group(2)
                if unit.startswith("km"):
                    fee = fee / 0.621371
                data["overage_fee_per_mile"] = round(fee, 4)
            except Exception:
                pass
        else:
            m = re.search(
                r"excess\s+kilometers\s+charge[\s\S]{0,300}?\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:cents)?\s*per\s*kilometer",
                normalized,
            )
            if not m:
                m = re.search(r"\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:cents)?\s*per\s*kilometer", normalized)
            if m:
                try:
                    fee = float(m.group(1))
                    if "cents" in m.group(0) and fee > 1:
                        fee = fee / 100.0
                    fee = fee / 0.621371
                    data["overage_fee_per_mile"] = round(fee, 4)
                except Exception:
                    pass
        # Force km→mile conversion if OCR matched per kilometer but regex extracted 0.1
        if data.get("overage_fee_per_mile") == 0.1 and "per kilometer" in normalized:
            data["overage_fee_per_mile"] = round(0.1 / 0.621371, 4)

        # Maximum kilometer/mileage allowance
        limit_match = re.search(
            r"maximum\s+(?:kilometer|kilometre|mileage)\s+allowance\s*(?:is|of|:|will\s+be)?\s*"
            r"(\d+(?:,\d{3})*)\s*(km|kilometers|miles|mile)\b",
            normalized,
        )
        if limit_match:
            try:
                limit = int(limit_match.group(1).replace(",", ""))
                unit = limit_match.group(2)
                if unit.startswith("km"):
                    limit = int(round(limit * 0.621371))
                # If term exists, interpret limit as total and normalize to annual
                term = data.get("lease_term_months")
                if term:
                    years = float(term) / 12.0
                    if years > 0:
                        limit = int(round(limit / years))
                data["mileage_limit_per_year"] = limit
            except Exception:
                pass
        else:
            limit = data.get("mileage_limit_per_year")
            if limit and "maximum kilometer allowance" in normalized:
                try:
                    limit = int(limit)
                    term = data.get("lease_term_months")
                    if term:
                        years = float(term) / 12.0
                        if years > 0:
                            limit = int(round((limit * 0.621371) / years))
                    data["mileage_limit_per_year"] = limit
                except Exception:
                    pass

        buyout_match = re.search(
            r"purchase\s+price\s+at\s+lease\s+maturity\s+will\s+be[^\d]{0,20}\$?\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
            normalized,
        )
        if buyout_match:
            try:
                data["buyout_price"] = float(buyout_match.group(1).replace(",", ""))
            except Exception:
                pass

        # Clause cleaning using section headings
        data.update(self._extract_clauses(text, data))

        return data

    def _extract_clauses(self, text: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract concise clause summaries by section headers.
        """
        raw = re.sub(r"\s+", " ", text)

        def section(section_num: str, title: str) -> Optional[str]:
            pattern = rf"{section_num}\.\s*{title}\s*(.+?)(?=\s+\d+\.\s+[A-Z])"
            m = re.search(pattern, raw, re.IGNORECASE)
            if not m:
                return None
            snippet = m.group(1).strip()
            return snippet[:300]

        clauses = {}
        insurance = section("9", "INSURANCE")
        if insurance:
            clauses["insurance_coverage"] = insurance

        warranty = section("13", "WARRANTY")
        if warranty:
            clauses["warranty_coverage"] = warranty

        early = section("17", "EARLY TERMINATION")
        if early:
            clauses["early_termination_policy"] = early

        maintenance = section("14", "MAINTENANCE")
        if maintenance:
            clauses["maintenance_clause"] = maintenance

        # Late fee: use line-based heuristic
        # Late fee: prefer explicit money/percent patterns, keep it short
        # Late fee: target explicit late payment charge lines, avoid optional service amounts
        # Prefer explicit "$X for each ... payment/cheque" pattern (late fees)
        m = re.search(
            r"charge\s+of\s*\$\s*([1-9]\d+(?:\.\d{2})?)\s+for\s+each\s+.*?(payment|cheque)",
            raw,
            re.IGNORECASE,
        )
        if m:
            clauses["late_fee_policy"] = f"${m.group(1)}"
        else:
            # Fall back to "late payment charges" window
            late = re.search(
                r"late\s+payment\s+charges?.{0,240}",
                raw,
                re.IGNORECASE,
            )
            if late:
                window = late.group(0)
                amt = re.search(r"\$\s*([1-9]\d+(?:\.\d{2})?)", window)
                pct = re.search(r"(\d{1,2})\s*%?\s*interest", window, re.IGNORECASE)
                if amt and pct:
                    clauses["late_fee_policy"] = f"${amt.group(1)} + {pct.group(1)}% interest"
                elif amt:
                    clauses["late_fee_policy"] = f"${amt.group(1)}"

        return clauses

    def _drop_residual_if_equals_buyout(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avoid misclassifying purchase option price as residual value amount.
        """
        residual = data.get("residual_value_amount")
        buyout = data.get("buyout_price")
        if residual is not None and buyout is not None:
            try:
                if float(residual) == float(buyout):
                    data["residual_value_amount"] = None
            except Exception:
                pass
        return data

    def _validate_and_create_contract_facts(self, data: Dict[str, Any]) -> Optional[ContractFacts]:
        """
        Validate extracted data and create ContractFacts instance.

        Args:
            data: Extracted data dictionary

        Returns:
            ContractFacts instance if valid, None otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = ['apr', 'monthly_payment', 'lease_term_months']
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                logger.warning(f"Missing required fields in extracted data: {missing}")
                raise RuntimeError(
                    "Extraction succeeded but required fields are missing: "
                    + ", ".join(missing)
                )

            # Create ContractFacts object (validation happens in the model)
            contract_facts = ContractFacts(**data)
            return contract_facts

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pipeline = ExtractPipeline()
    # Example: pipeline.run("path/to/lease_agreement.pdf")
