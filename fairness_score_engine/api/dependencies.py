"""
API dependencies for the Car Lease Review AI Assistant
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / '.env')

from database.db import ContractFactsDB
from pipelines.extract_pipeline import ExtractPipeline
from pipelines.scoring_pipeline import ScoringPipeline

def get_db() -> ContractFactsDB:
    """Dependency to get database instance"""
    return ContractFactsDB()

def get_extract_pipeline() -> ExtractPipeline:
    """Dependency to get extraction pipeline instance with LLM and OCR support"""
    # Read env at call time to avoid stale values
    tesseract_cmd = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    groq_api_key = os.getenv('GROQ_API_KEY')
    return ExtractPipeline(
        tesseract_cmd=tesseract_cmd,
        openai_api_key=groq_api_key  # Using Groq's free API
    )


def get_scoring_pipeline() -> ScoringPipeline:
    """Dependency to get scoring pipeline instance."""
    return ScoringPipeline()
