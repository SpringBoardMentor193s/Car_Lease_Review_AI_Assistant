from fastapi import FastAPI, UploadFile, File
import shutil
import os

from backend.ocr.ocr_utils import extract_text_from_pdf
from backend.db.database import init_db, save_contract, save_sla_data
from backend.extraction.rule_extractor import extract_sla_fields


app = FastAPI()

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

init_db()


@app.get("/")
def root():
    return {"status": "Backend running"}


@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    extracted_text = extract_text_from_pdf(file_path)

    # Save contract text
    contract_id = save_contract(file.filename, extracted_text)

    # SLA extraction (rule-based, full schema)
    sla_data = extract_sla_fields(extracted_text)

    # Save SLA data
    save_sla_data(contract_id, sla_data)

    return {
        "message": "File uploaded, processed, and SLA extracted",
        "contract_id": contract_id,
        "file_name": file.filename,
        "sla_data": sla_data,
        "preview": extracted_text[:500]
    }
