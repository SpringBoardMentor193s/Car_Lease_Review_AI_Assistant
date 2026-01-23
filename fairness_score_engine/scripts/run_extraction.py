#!/usr/bin/env python3
"""
Script to run the extraction pipeline on a car lease PDF.

Usage:
    python scripts/run_extraction.py <pdf_path>

Example:
    python scripts/run_extraction.py path/to/car_lease.pdf
"""

import sys
import logging
from pathlib import Path

# Add the parent directory to the path to import fairness_score_engine
sys.path.insert(0, str(Path(__file__).parent.parent))

from fairness_score_engine.pipelines.extract_pipeline import ExtractPipeline

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_extraction.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Check if PDF file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' does not exist.")
        sys.exit(1)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the extraction pipeline
    pipeline = ExtractPipeline()
    record_id = pipeline.run(pdf_path)

    if record_id:
        print(f"Successfully processed PDF and stored contract facts with ID: {record_id}")
    else:
        print("Failed to process PDF. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()