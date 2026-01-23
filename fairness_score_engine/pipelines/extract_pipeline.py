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

logger = logging.getLogger(__name__)

class ExtractPipeline:
    def __init__(self, db_path: str = "contract_facts.db"):
        self.extractor = PDFExtractor()
        self.db = ContractFactsDB(db_path)

    def run(self, pdf_path: str) -> Optional[int]:
        """
        Run the extraction pipeline on a PDF file.

        Args:
            pdf_path: Path to the PDF file to process

        Returns:
            The database ID of the inserted record, or None if extraction/validation failed
        """
        try:
            logger.info(f"Starting extraction for PDF: {pdf_path}")

            # Extract data from PDF
            extracted_data = self.extractor.extract_from_pdf(pdf_path)
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
