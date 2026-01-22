from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services import ocr_service, llm_service, fairness_service, market_service
import json

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)

@router.post("/upload", response_model=models.ContractResponse)
async def upload_contract(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Read File
    contents = await file.read()
    
    # 2. OCR
    text = ocr_service.extract_text_from_file(contents, file.filename)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file.")

    # 3. LLM Clause Extraction
    clauses = llm_service.llm_service.extract_clauses(text)
    
    # 4. Market Data (Heuristic/Mock based on clauses)
    # Try to find Make/Model in extracted text or clauses
    make = "Toyota" # Placeholder/Logic to extract from text needed if not in JSON
    model = "Camry"
    year = 2024
    if "Toyota" in text: make="Toyota"
    if "Camry" in text: model="Camry"
    
    price_min, price_max = market_service.get_market_price(make, model, year)
    vin_info = market_service.get_vin_info("MOCK_VIN")

    # 5. Fairness Score
    fairness = fairness_service.calculate_fairness_score(clauses)

    # 6. Save to DB
    db_contract = models.ContractBase(
        filename=file.filename,
        extracted_text=text,
        clauses=clauses,
        fairness_score=fairness["score"],
        fairness_explanation=fairness["explanation"],
        market_price_min=price_min,
        market_price_max=price_max,
        vin_info=vin_info
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    
    return db_contract

@router.get("/contracts/{contract_id}", response_model=models.ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(models.ContractBase).filter(models.ContractBase.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
