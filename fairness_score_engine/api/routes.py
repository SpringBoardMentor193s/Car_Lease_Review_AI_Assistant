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
    ScoreResult,
    FairnessReportResponse,
    OcrHealthResponse,
)
from .dependencies import get_extract_pipeline, get_db, get_scoring_pipeline
from database.db import ContractFactsDB
from pipelines.extract_pipeline import ExtractPipeline
from pipelines.scoring_pipeline import ScoringPipeline
from engine.vin_report import generate_vin_report
from models.contract_facts import ContractFacts
import os
import shutil
from engine.pdf_extractor import OCR_AVAILABLE

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Configuration for PDF storage
SAVE_ORIGINAL_PDFS = True  # Set to False to delete PDFs after processing

def _with_mileage_km(extracted_data: dict, remove_miles: bool = False) -> dict:
    data = dict(extracted_data)
    miles = data.get("mileage_limit_per_year")
    if miles is None:
        return data
    try:
        km = int(round(float(miles) / 0.621371))
    except Exception:
        return data
    data["mileage_limit_per_year_km"] = km
    data["mileage_limit_per_year_display"] = f"{km} km"
    if remove_miles:
        data.pop("mileage_limit_per_year", None)
    return data

def _with_overage_km(extracted_data: dict, remove_miles: bool = False) -> dict:
    data = dict(extracted_data)
    miles_fee = data.get("overage_fee_per_mile")
    if miles_fee is None:
        return data
    try:
        km_fee = float(miles_fee) * 0.621371
    except Exception:
        return data
    data["overage_fee_per_km"] = round(km_fee, 4)
    data["overage_fee_per_km_display"] = f"{round(km_fee, 4)} per km"
    if remove_miles:
        data.pop("overage_fee_per_mile", None)
    return data

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
        response_data = _with_mileage_km(extracted_data, remove_miles=True)
        response_data = _with_overage_km(response_data, remove_miles=True)

        # Clean up temp file if not saving permanently
        if not SAVE_ORIGINAL_PDFS and temp_path.exists():
            temp_path.unlink()

        return ExtractionResult(
            record_id=record_id,
            extracted_data=response_data,
        )

    except RuntimeError as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/score", response_model=ScoreResult)
async def score_contract(
    file: UploadFile = File(...),
    use_llm: bool = True,
    use_ocr: bool = False,
    pipeline: ExtractPipeline = Depends(get_extract_pipeline),
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline),
):
    """
    Upload a PDF, extract contract facts, and return a fairness score.

    - **file**: PDF file containing the car lease agreement
    - **use_llm**: Use LLM (Llama 3) for extraction (recommended for real contracts, default: True)
    - **use_ocr**: Force OCR for scanned PDFs (default: False)
    - Returns extraction results and fairness score report
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    temp_path = UPLOAD_DIR / f"temp_{file.filename}"
    final_path = None

    if SAVE_ORIGINAL_PDFS:
        import time
        timestamp = int(time.time())
        final_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if final_path:
            shutil.move(str(temp_path), str(final_path))
            processing_path = final_path
        else:
            processing_path = temp_path

        record_id = pipeline.run(str(processing_path), use_ocr=use_ocr, use_llm=use_llm)
        if record_id is None:
            raise HTTPException(status_code=422, detail="Failed to extract contract facts from PDF")

        db = ContractFactsDB()
        records = db.get_all_contract_facts()
        extracted_data = next((r for r in records if r['id'] == record_id), {})
        response_data = _with_mileage_km(extracted_data, remove_miles=True)
        response_data = _with_overage_km(response_data, remove_miles=True)

        if not extracted_data:
            raise HTTPException(status_code=500, detail="Extracted record not found after insert")

        # Build ContractFacts from extracted data (strip DB fields)
        fact_fields = set(ContractFacts.__fields__.keys())
        facts_payload = {k: v for k, v in extracted_data.items() if k in fact_fields}
        fairness_report = scoring_pipeline.run(facts_payload)

        if not SAVE_ORIGINAL_PDFS and temp_path.exists():
            temp_path.unlink()

        return ScoreResult(
            record_id=record_id,
            fairness_report=FairnessReportResponse(**fairness_report.dict()),
        )

    except HTTPException:
        if temp_path.exists():
            temp_path.unlink()
        raise
    except RuntimeError as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

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


@router.get("/health/ocr", response_model=OcrHealthResponse)
async def ocr_health():
    """Check OCR dependencies and configuration."""
    tesseract_cmd = os.getenv("TESSERACT_CMD", "")
    tesseract_exists = bool(tesseract_cmd) and os.path.exists(tesseract_cmd)
    pdf2image_available = OCR_AVAILABLE
    poppler_on_path = bool(shutil.which("pdfinfo")) and bool(shutil.which("pdftoppm"))
    poppler_hint = (
        "Install Poppler and add its bin folder to PATH (e.g., C:\\Program Files\\poppler\\Library\\bin)"
        if not poppler_on_path
        else ""
    )

    return OcrHealthResponse(
        tesseract_cmd=tesseract_cmd or "",
        tesseract_exists=tesseract_exists,
        pdf2image_available=pdf2image_available,
        poppler_on_path=poppler_on_path,
        poppler_hint=poppler_hint,
    )
