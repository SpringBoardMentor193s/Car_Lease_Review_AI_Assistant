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

# Configuration from environment variables
TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def get_db() -> ContractFactsDB:
    """Dependency to get database instance"""
    return ContractFactsDB()

def get_extract_pipeline() -> ExtractPipeline:
    """Dependency to get extraction pipeline instance with LLM and OCR support"""
    return ExtractPipeline(
        tesseract_cmd=TESSERACT_CMD,
        openai_api_key=GROQ_API_KEY  # Using Groq's free API
    )
