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
from engine.vin_report import decode_vin
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
            text_layer = self.extractor._extract_with_pdfplumber(pdf_path)
            
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
            extracted_data = self._extract_pricing_context(text, extracted_data)
            # If OCR was forced but PDF text layer exists, prefer text-layer identity signals
            # (VIN/year/make/model are often cleaner in embedded text than OCR output).
            if use_ocr and self.extractor._has_meaningful_text(text_layer):
                extracted_data = self._extract_pricing_context(text_layer, extracted_data)
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

    def _extract_pricing_context(self, text: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract optional pricing-context fields that improve dynamic buyout estimation.
        """
        normalized = re.sub(r"\s+", " ", text).strip()
        normalized_lower = normalized.lower()

        self._normalize_or_replace_vin(normalized, data)

        address_parts = self._extract_address_components(normalized)
        if address_parts:
            if not data.get("lessee_city") and address_parts.get("city"):
                data["lessee_city"] = address_parts["city"]
            if not data.get("lessee_state") and address_parts.get("state_or_province"):
                data["lessee_state"] = address_parts["state_or_province"]
            if not data.get("lessee_zip") and address_parts.get("postal_code"):
                data["lessee_zip"] = address_parts["postal_code"]

        if not data.get("lessee_state"):
            state = self._extract_us_state(normalized)
            if state:
                data["lessee_state"] = state

        if not data.get("lessee_zip"):
            zip_code = self._extract_zip(normalized)
            if zip_code:
                data["lessee_zip"] = zip_code

        if not data.get("lessee_city"):
            city = self._extract_city(normalized)
            if city:
                data["lessee_city"] = city

        if data.get("vin"):
            self._backfill_vehicle_identity_from_vin(data)
        self._backfill_vehicle_identity_from_table(normalized, data)

        if not data.get("vehicle_mileage"):
            mileage = self._extract_vehicle_mileage(normalized_lower)
            if mileage is not None:
                data["vehicle_mileage"] = mileage

        if not data.get("lease_region"):
            region = self._extract_lease_region(normalized_lower)
            if region:
                data["lease_region"] = region

        if not data.get("vehicle_condition"):
            condition = self._extract_vehicle_condition(normalized_lower)
            if condition:
                data["vehicle_condition"] = condition

        return data

    def _normalize_or_replace_vin(self, normalized_text: str, data: Dict[str, Any]) -> None:
        """
        Keep VIN only if it is probable, otherwise attempt fresh extraction from text.
        """
        vin = data.get("vin")
        if vin:
            vin_up = str(vin).strip().upper()
            vin_up = self._normalize_ocr_vin_candidate(vin_up)
            if self._is_probable_vin(vin_up):
                data["vin"] = vin_up
                return
            data["vin"] = None

        extracted = self._extract_vin(normalized_text)
        if extracted:
            data["vin"] = extracted

    def _extract_us_state(self, text: str) -> Optional[str]:
        patterns = [
            r"state of\s+([A-Za-z ]{2,30})\b",
            r"lessee(?:'s)?\s+address[\s\S]{0,120}?\b([A-Z]{2})\s+\d{5}(?:-\d{4})?\b",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if not m:
                continue
            candidate = m.group(1).strip()
            if len(candidate) == 2 and candidate.isalpha():
                return candidate.upper()
            words = candidate.split()
            if words:
                return words[-1].title()
        return None

    def _extract_lease_region(self, text_lower: str) -> Optional[str]:
        region_keywords = {
            "urban": ("urban", "metro", "metropolitan", "city center"),
            "suburban": ("suburban", "suburb"),
            "rural": ("rural", "county"),
            "coastal": ("coastal", "shore", "beach area"),
        }
        for region, keys in region_keywords.items():
            if any(k in text_lower for k in keys):
                return region
        city_region_map = {
            "mumbai": "urban",
            "delhi": "urban",
            "bangalore": "urban",
            "new york": "urban",
            "los angeles": "urban",
        }
        for city, region in city_region_map.items():
            if city in text_lower:
                return region
        return None

    def _extract_vehicle_condition(self, text_lower: str) -> Optional[str]:
        if re.search(r"\b(excellent|like new|mint)\b", text_lower):
            return "excellent"
        if re.search(r"\b(good|well maintained)\b", text_lower):
            return "good"
        if re.search(r"\b(fair|average condition)\b", text_lower):
            return "fair"
        if re.search(r"\b(poor|heavy wear|major damage)\b", text_lower):
            return "poor"
        return None

    def _extract_city(self, text: str) -> Optional[str]:
        patterns = [
            r"city of\s+([A-Za-z][A-Za-z\s\-]{1,40})\b",
            r"lessee(?:'s)?\s+address[\s\S]{0,160}?,\s*([A-Za-z][A-Za-z\s\-]{1,40})\s*,\s*[A-Za-z]{2,}",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return " ".join(m.group(1).split()).title()
        return None

    def _extract_zip(self, text: str) -> Optional[str]:
        # Prefer Canadian postal codes first (A1A 1A1 / A1A1A1).
        m = re.search(r"\b([A-Z]\d[A-Z]\s?\d[A-Z]\d)\b", text, re.IGNORECASE)
        if m:
            return m.group(1).replace(" ", "").upper()

        # Then US ZIP/ZIP+4.
        m = re.search(r"\b(\d{5}(?:-\d{4})?)\b", text)
        if m:
            return m.group(1)
        return None

    def _extract_vin(self, text: str) -> Optional[str]:
        upper = text.upper()

        # First pass: strict VIN pattern.
        m = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", upper)
        if m:
            candidate = m.group(1)
            if self._is_probable_vin(candidate):
                return candidate

        # Second pass: near VIN labels, tolerate OCR separators/noise.
        for label in ("VIN", "VEHICLE IDENTIFICATION NUMBER"):
            idx = upper.find(label)
            if idx == -1:
                continue
            window = upper[idx: idx + 120]
            cleaned = re.sub(r"[^A-Z0-9]", "", window)
            # Keep only tail after label token to avoid picking chars from label text itself.
            cleaned = cleaned.replace("VEHICLEIDENTIFICATIONNUMBER", "").replace("VIN", "")
            if len(cleaned) < 17:
                continue
            # Try every 17-char slice and normalize common OCR confusions.
            for i in range(0, len(cleaned) - 16):
                candidate = cleaned[i:i + 17]
                normalized = self._normalize_ocr_vin_candidate(candidate)
                if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", normalized) and self._is_probable_vin(normalized):
                    return normalized

        return None

    def _normalize_ocr_vin_candidate(self, value: str) -> str:
        """
        Normalize common OCR mistakes for VIN strings.
        VIN must not contain I, O, Q.
        """
        # Replace frequent OCR substitutions in VIN-like tokens.
        v = value.replace("I", "1").replace("O", "0").replace("Q", "0")
        return v

    def _is_probable_vin(self, value: str) -> bool:
        """
        Guard against OCR false positives:
        - VIN should be 17 chars with mixed alnum profile
        - avoid obvious word-like artifacts
        """
        if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", value):
            return False
        digit_count = sum(1 for c in value if c.isdigit())
        alpha_count = 17 - digit_count
        if digit_count < 4 or alpha_count < 3:
            return False
        # Reject common OCR junk tokens from legal text.
        bad_chunks = ("FEDERAL", "TAX", "SOCIAL", "NUMBER")
        if any(chunk in value for chunk in bad_chunks):
            return False
        if not self._passes_vin_check_digit(value):
            return False
        return True

    def _passes_vin_check_digit(self, vin: str) -> bool:
        """
        Validate VIN check digit (position 9) per ISO 3779/NHTSA logic.
        """
        if len(vin) != 17:
            return False
        translit = {
            "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
            "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
            "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
            "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        }
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        try:
            total = 0
            for i, ch in enumerate(vin):
                total += translit[ch] * weights[i]
            remainder = total % 11
            expected = "X" if remainder == 10 else str(remainder)
            return vin[8] == expected
        except Exception:
            return False

    def _backfill_vehicle_identity_from_vin(self, data: Dict[str, Any]) -> None:
        """
        If VIN exists, decode it once and fill missing year/make/model fields.
        """
        if data.get("vehicle_year") and data.get("vehicle_make") and data.get("vehicle_model"):
            return
        vin = str(data.get("vin", "")).strip()
        if len(vin) != 17:
            return
        try:
            decoded = decode_vin(vin)
        except Exception:
            return
        # If decode failed, drop VIN so downstream pricing doesn't use bad identity.
        if decoded.get("error"):
            data["vin"] = None
            return
        # If decode returns no usable identity, treat as bad VIN.
        if not decoded.get("model_year") and not decoded.get("make") and not decoded.get("model"):
            data["vin"] = None
            return
        if not data.get("vehicle_year") and decoded.get("model_year"):
            try:
                data["vehicle_year"] = int(decoded.get("model_year"))
            except Exception:
                pass
        if not data.get("vehicle_make") and decoded.get("make"):
            data["vehicle_make"] = str(decoded.get("make")).strip().lower()
        if not data.get("vehicle_model") and decoded.get("model"):
            data["vehicle_model"] = str(decoded.get("model")).strip().lower()

    def _backfill_vehicle_identity_from_table(self, text: str, data: Dict[str, Any]) -> None:
        """
        Recover year/make/model from common lease-table rows in OCR text:
        e.g. USED 2003 HONDA ACCORD ... 1HGCM...
        """
        if data.get("vehicle_year") and data.get("vehicle_make") and data.get("vehicle_model"):
            return

        # Try row format with explicit columns.
        row_match = re.search(
            r"(?:NEW|USED|DEMO)\s+(\d{4})\s+([A-Z][A-Z0-9\-]{1,20})\s+([A-Z][A-Z0-9\- ]{1,30})\s+(?:[A-Z0-9\- ]{0,20})\s+([A-HJ-NPR-Z0-9]{17})",
            text.upper(),
        )
        if row_match:
            year, make, model, vin = row_match.groups()
            if not data.get("vehicle_year"):
                try:
                    data["vehicle_year"] = int(year)
                except Exception:
                    pass
            if not data.get("vehicle_make"):
                data["vehicle_make"] = make.strip().lower()
            if not data.get("vehicle_model"):
                data["vehicle_model"] = model.strip().lower()
            if not data.get("vin") and self._is_probable_vin(vin):
                data["vin"] = vin
            return

        # Try independent field labels.
        if not data.get("vehicle_year"):
            m = re.search(r"\b(?:YEAR)\s*[:\-]?\s*(\d{4})\b", text, re.IGNORECASE)
            if m:
                try:
                    data["vehicle_year"] = int(m.group(1))
                except Exception:
                    pass
        if not data.get("vehicle_make"):
            m = re.search(r"\b(?:MAKE)\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\-]{1,20})\b", text, re.IGNORECASE)
            if m:
                mk = m.group(1).strip().lower()
                if mk not in {"model", "year", "code", "vehicle"}:
                    data["vehicle_make"] = mk
        if not data.get("vehicle_model"):
            m = re.search(r"\b(?:MODEL)\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\- ]{1,30})\b", text, re.IGNORECASE)
            if m:
                md = m.group(1).strip().lower()
                if md not in {"code", "model code", "vehicle", "vehicle identification"}:
                    # Trim if OCR captured following header words.
                    md = re.split(r"\b(model\s+code|vehicle\s+identification)\b", md)[0].strip()
                    if md:
                        data["vehicle_model"] = md

    def _extract_vehicle_mileage(self, text_lower: str) -> Optional[int]:
        patterns = [
            r"\b(?:odometer|mileage|miles)\s*(?:reading|at delivery|is|:)?\s*(\d{1,3}(?:,\d{3})+|\d{4,7})\b",
            r"\b(\d{1,3}(?:,\d{3})+|\d{4,7})\s*miles\b",
            r"\b(\d{1,3}(?:,\d{3})+|\d{4,7})\s*km\b",
        ]
        for p in patterns:
            m = re.search(p, text_lower, re.IGNORECASE)
            if not m:
                continue
            try:
                value = int(m.group(1).replace(",", ""))
                if " km" in m.group(0).lower():
                    value = int(round(value * 0.621371))
                return value
            except Exception:
                continue
        return None

    def _extract_address_components(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract city/province/postal from address-like strings.
        Supports both Canadian and US style:
          - Address: ..., Vancouver, BC, V6A 2B3
          - Address: ..., Seattle, WA, 98101
        """
        # Focus on address lines/segments.
        for m in re.finditer(r"address\s*:\s*([^\n\r]{10,220})", text, re.IGNORECASE):
            segment = m.group(1).strip()
            parsed = self._parse_city_state_postal(segment)
            if parsed:
                return parsed

        # Fallback: parse any comma-separated city/state/postal sequence.
        parsed = self._parse_city_state_postal(text)
        return parsed

    def _parse_city_state_postal(self, text: str) -> Optional[Dict[str, str]]:
        patterns = [
            # Canadian: City, BC, V6A 2B3
            r",\s*([A-Za-z][A-Za-z .'\-]{1,40})\s*,\s*([A-Z]{2})\s*,\s*([A-Z]\d[A-Z]\s?\d[A-Z]\d)\b",
            # US: City, WA, 98101 or 98101-1234
            r",\s*([A-Za-z][A-Za-z .'\-]{1,40})\s*,\s*([A-Z]{2})\s*,\s*(\d{5}(?:-\d{4})?)\b",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if not m:
                continue
            city = " ".join(m.group(1).split()).title()
            state_or_province = m.group(2).upper()
            postal = m.group(3).replace(" ", "").upper()
            return {
                "city": city,
                "state_or_province": state_or_province,
                "postal_code": postal,
            }
        return None

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
