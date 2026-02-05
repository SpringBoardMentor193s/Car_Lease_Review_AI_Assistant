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
