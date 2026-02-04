"""
API routes for the Car Lease Review AI Assistant
"""

import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from .schemas import (
    ExtractionResult,
    ExtractionError,
    ContractFactsResponse,
    VinReportResponse,
)
from .dependencies import get_extract_pipeline, get_db
from database.db import ContractFactsDB
from pipelines.extract_pipeline import ExtractPipeline
from engine.vin_report import generate_vin_report

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Configuration for PDF storage
SAVE_ORIGINAL_PDFS = True  # Set to False to delete PDFs after processing

@router.post("/extract", response_model=ExtractionResult)
async def extract_contract_facts(
    file: UploadFile = File(...),
    use_llm: bool = True,
    use_ocr: bool = False,
    pipeline: ExtractPipeline = Depends(get_extract_pipeline)
):
    """
    Upload a PDF and extract contract facts.

    - **file**: PDF file containing the car lease agreement
    - **use_llm**: Use LLM (Llama 3) for extraction (recommended for real contracts, default: True)
    - **use_ocr**: Force OCR for scanned PDFs (default: False)
    - Returns extraction results and database record ID
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save uploaded file temporarily
    temp_path = UPLOAD_DIR / f"temp_{file.filename}"
    final_path = None

    if SAVE_ORIGINAL_PDFS:
        # Save with timestamp for uniqueness
        import time
        timestamp = int(time.time())
        final_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Move to final location if saving
        if final_path:
            shutil.move(str(temp_path), str(final_path))
            processing_path = final_path
        else:
            processing_path = temp_path

        # Run extraction pipeline
        record_id = pipeline.run(str(processing_path), use_ocr=use_ocr, use_llm=use_llm)

        if record_id is None:
            raise HTTPException(status_code=422, detail="Failed to extract contract facts from PDF")

        # Get the extracted data for response
        db = ContractFactsDB()
        records = db.get_all_contract_facts()
        extracted_data = next((r for r in records if r['id'] == record_id), {})

        # Clean up temp file if not saving permanently
        if not SAVE_ORIGINAL_PDFS and temp_path.exists():
            temp_path.unlink()

        return ExtractionResult(
            record_id=record_id,
            extracted_data=extracted_data
        )

    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/contracts", response_model=List[ContractFactsResponse])
async def get_all_contracts(db: ContractFactsDB = Depends(get_db)):
    """Retrieve all stored contract facts."""
    try:
        records = db.get_all_contract_facts()
        return [ContractFactsResponse(**record) for record in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@router.get("/contracts/{record_id}", response_model=ContractFactsResponse)
async def get_contract_by_id(
    record_id: int,
    db: ContractFactsDB = Depends(get_db),
):
    """Retrieve a specific contract by ID."""
    try:
        records = db.get_all_contract_facts()
        record = next((r for r in records if r['id'] == record_id), None)
        if not record:
            raise HTTPException(status_code=404, detail="Contract not found")
        return ContractFactsResponse(**record)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@router.get("/vin-report/{vin}", response_model=VinReportResponse)
async def get_vin_report(vin: str):
    """Generate a VIN-based vehicle history and risk report.

    - **vin**: 17-character Vehicle Identification Number
    """
    try:
        report = generate_vin_report(vin)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VIN report generation failed: {str(e)}")
