from fastapi import FastAPI, UploadFile, File
import shutil
import os

from backend.ocr.ocr_utils import extract_text_from_pdf
from backend.db.database import init_db, save_contract, save_sla_data
from backend.extraction.rule_extractor import extract_sla_fields
from backend.extraction.llm_extractor import extract_sla_with_llm
from backend.extraction.vin_extractor import extract_vin
from backend.services.nhtsa_service import get_vehicle_details_from_vin
from backend.analysis.risk_engine import calculate_lease_risk  # ✅ NEW


app = FastAPI()

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

init_db()


@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(file_path)

    contract_id = save_contract(file.filename, extracted_text)

    rule_sla = extract_sla_fields(extracted_text)
    llm_sla = extract_sla_with_llm(extracted_text)

    final_sla = {}
    for key in rule_sla:
        final_sla[key] = rule_sla[key] if rule_sla[key] is not None else llm_sla.get(key)

    save_sla_data(contract_id, final_sla)

    vin = extract_vin(extracted_text)
    vehicle_data = get_vehicle_details_from_vin(vin)

    # ✅ RISK ENGINE
    risk_assessment = calculate_lease_risk(final_sla, vehicle_data)

    return {
        "message": "File uploaded, processed, SLA, vehicle data & risk assessed",
        "contract_id": contract_id,
        "file_name": file.filename,
        "vin": vin,
        "vehicle_data": vehicle_data,
        "sla_data": final_sla,
        "risk_assessment": risk_assessment,
        "preview": extracted_text[:500]
    }
