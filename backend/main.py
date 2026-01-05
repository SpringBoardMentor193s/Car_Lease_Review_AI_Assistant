from fastapi import FastAPI, UploadFile, File
import shutil
import os

from backend.ocr.ocr_utils import extract_text_from_pdf
from backend.db.database import init_db, save_contract


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

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    extracted_text = extract_text_from_pdf(file_path)

    # Save to DB
    save_contract(file.filename, extracted_text)

    return {
        "message": "File uploaded and processed",
        "file_name": file.filename,
        "preview": extracted_text[:500]
    }
