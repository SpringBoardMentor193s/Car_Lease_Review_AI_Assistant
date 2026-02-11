import os
import json
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from .database import Base, engine, SessionLocal
from .models import Contract
from .ocr import extract_text_from_pdf, extract_text_from_image
from .llm_service import extract_sla
from typing import cast, Any
from .vin_service import lookup_vin
from .negotiation_service import generate_negotiation_advice
from .pricing_service import get_comprehensive_pricing
from .fairness_score import calculate_fairness_score

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Car Lease Contract Reviewer")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"status": "API running"}

# -------- Milestone 1: Upload + OCR --------


@app.post("/upload-contract/")
async def upload_contract(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, str(file.filename))

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if (file.filename or "").lower().endswith(".pdf"):
        text = extract_text_from_pdf(path)
    else:
        text = extract_text_from_image(path)

    db = SessionLocal()
    contract = Contract(filename=file.filename, extracted_text=text)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    db.close()

    return {
        "contract_id": contract.id,
        "preview_text": text[:500]
    }

# -------- Milestone 2: SLA Extraction --------


@app.post("/extract-sla/{contract_id}")
def extract_sla_api(contract_id: int):
    db = SessionLocal()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    sla = extract_sla(contract.extracted_text)
    # SQLAlchemy instance attribute typing can be narrow; cast to Any for assignment
    cast(Any, contract).sla_json = json.dumps(sla)

    db.commit()
    db.close()

    return {"contract_id": contract_id, "sla": sla}


@app.get("/vin/{vin}")
def vin_lookup(vin: str):
    return lookup_vin(vin)


@app.get("/contract-summary/{contract_id}")
def contract_summary(contract_id: int, vin: str):
    db = SessionLocal()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contract not found")
    db.close()

    sla = json.loads(str(contract.sla_json)) if contract.sla_json else {}

    return {
        "sla": sla,
        "vehicle": lookup_vin(vin)
    }

# -------- Milestone 3: Negotiation Assistant --------


@app.get("/negotiation/{contract_id}")
def negotiation(contract_id: int):
    db = SessionLocal()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contract not found")
    db.close()

    advice = generate_negotiation_advice(contract.sla_json or "{}")
    return {"negotiation_advice": advice}


# -------- Milestone 4: Pricing APIs & Fairness Score --------


@app.get("/pricing/{vin}")
def get_pricing(vin: str):
    """
    Fetch fair market pricing for a vehicle using multiple APIs.
    
    Integrates:
    - NHTSA API for vehicle specs
    - Edmunds pricing data
    - TrueCar market data
    """
    pricing_data = get_comprehensive_pricing(vin)
    return pricing_data


@app.post("/fairness-score/{contract_id}")
def compute_fairness_score(contract_id: int, vin: str = None):
    """
    Calculate Contract Fairness Score (0-100) with detailed breakdown.
    
    Evaluates:
    - Monthly payment competitiveness
    - Interest rate fairness
    - Mileage allowance
    - Early termination fees
    - Penalty structure
    - Market price comparison (if VIN provided)
    
    Scoring: 0-100 where 80+ is EXCELLENT, 65-79 is GOOD, etc.
    """
    db = SessionLocal()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    sla_json = contract.sla_json or "{}"
    fairness_result = calculate_fairness_score(sla_json, vin)
    
    # Update contract with fairness score
    cast(Any, contract).fairness_score = fairness_result["fairness_score"]
    cast(Any, contract).fairness_level = fairness_result["fairness_level"]
    db.commit()
    db.close()

    return {
        "contract_id": contract_id,
        "fairness_score": fairness_result["fairness_score"],
        "fairness_level": fairness_result["fairness_level"],
        "breakdown": fairness_result["breakdown"],
        "recommendations": fairness_result["recommendations"]
    }


@app.get("/full-report/{contract_id}")
def get_full_report(contract_id: int, vin: str = None):
    """
    Get comprehensive contract review report including:
    - SLA extraction
    - Negotiation advice
    - Pricing data
    - Fairness score
    """
    db = SessionLocal()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        db.close()
        raise HTTPException(status_code=404, detail="Contract not found")
    db.close()

    sla = json.loads(str(contract.sla_json)) if contract.sla_json else {}
    advice = generate_negotiation_advice(contract.sla_json or "{}")
    fairness = calculate_fairness_score(contract.sla_json or "{}", vin)
    pricing = get_comprehensive_pricing(vin) if vin else {}
    
    return {
        "contract_id": contract_id,
        "filename": contract.filename,
        "sla_extraction": sla,
        "negotiation_advice": advice,
        "pricing_data": pricing,
        "fairness_score": fairness["fairness_score"],
        "fairness_level": fairness["fairness_level"],
        "fairness_breakdown": fairness["breakdown"],
        "recommendations": fairness["recommendations"]
    }

