#!/usr/bin/env python3
r"""
Script to run the extraction pipeline on a car lease PDF.

Usage:
    python scripts/run_extraction.py <pdf_path> [--ocr] [--llm]

Options:
    --ocr   Force OCR extraction for scanned PDFs
    --llm   Use LLM (GPT) for extraction (recommended for real contracts)

Example:
    python scripts/run_extraction.py path/to/car_lease.pdf
    python scripts/run_extraction.py path/to/scanned_lease.pdf --ocr
    python scripts/run_extraction.py path/to/real_contract.pdf --llm

Environment Variables:
    TESSERACT_CMD: Path to tesseract executable (default: C:\Program Files\Tesseract-OCR\tesseract.exe)
    GROQ_API_KEY: Groq API key for free LLM extraction (get at https://console.groq.com/keys)
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pipelines.extract_pipeline import ExtractPipeline

# Configuration from environment variables (loaded from .env)
TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_extraction.py <pdf_path> [--ocr] [--llm]")
        print("\nOptions:")
        print("  --ocr   Force OCR extraction for scanned PDFs")
        print("  --llm   Use LLM (Llama 3) for extraction (recommended for real contracts)")
        print("\nEnvironment Variables:")
        print("  GROQ_API_KEY: Required for --llm mode (free at https://console.groq.com/keys)")
        sys.exit(1)

    pdf_path = sys.argv[1]
    use_ocr = '--ocr' in sys.argv
    use_llm = '--llm' in sys.argv

    # Check if PDF file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' does not exist.")
        sys.exit(1)
    
    # Check for Groq API key if LLM mode is requested
    if use_llm and not GROQ_API_KEY:
        print("Error: --llm mode requires GROQ_API_KEY environment variable.")
        print("Get a FREE key at: https://console.groq.com/keys")
        print("Then set it with: $env:GROQ_API_KEY = 'your-api-key'")
        sys.exit(1)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the extraction pipeline
    pipeline = ExtractPipeline(
        tesseract_cmd=TESSERACT_CMD,
        openai_api_key=GROQ_API_KEY  # Using Groq's free API
    )
    record_id = pipeline.run(pdf_path, use_ocr=use_ocr, use_llm=use_llm)

    if record_id:
        print(f"Successfully processed PDF and stored contract facts with ID: {record_id}")
    else:
        print("Failed to process PDF. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()