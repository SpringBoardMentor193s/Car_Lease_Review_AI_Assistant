"""
Extract Pipeline for Car Lease Review AI Assistant

This module handles the extraction of SLA parameters from uploaded PDF documents,
validates the data against the contract facts schema, and stores the results in the database.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
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
            
            # Choose extraction method
            if use_llm and self.llm_extractor:
                logger.info("Using LLM extraction for complex document")
                extracted_data = self.llm_extractor.extract_fields(text)
            else:
                # Use regex-based extraction
                extracted_data = self.extractor.extract_fields(text)
            
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

        except Exception as e:
            logger.error(f"Error in extraction pipeline: {e}")
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
            if not all(field in data and data[field] is not None for field in required_fields):
                logger.warning("Missing required fields in extracted data")
                return None

            # Create ContractFacts object (validation happens in the model)
            contract_facts = ContractFacts(**data)
            return contract_facts

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pipeline = ExtractPipeline()
    # Example: pipeline.run("path/to/lease_agreement.pdf")
