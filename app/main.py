from fastapi import FastAPI, UploadFile, File
import shutil
import os

from .database import Base, engine, SessionLocal
from .models import Contract
from .ocr import extract_text_from_pdf, extract_text_from_image

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Car Contract Analysis API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-contract/")
async def upload_contract(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file.filename.endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_path)
    else:
        extracted_text = extract_text_from_image(file_path)

    db = SessionLocal()
    contract = Contract(
        filename=file.filename,
        extracted_text=extracted_text
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    db.close()

    return {
        "message": "Contract uploaded & text extracted successfully",
        "contract_id": contract.id,
        "preview_text": extracted_text[:500]
    }
@app.get("/")
def root():
    return {"status": "Car Contract Analysis API running"}
