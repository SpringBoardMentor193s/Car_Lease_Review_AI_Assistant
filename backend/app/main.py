from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from backend.pipeline.process_contract import process_contract

app = FastAPI(title="Car Lease Contract AI")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_contracts"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def health_check():
    return {"status": "Backend is running"}


@app.post("/analyze-contract")
async def analyze_contract(file: UploadFile = File(...)):
    """
    Upload a lease/loan contract PDF and get analysis.
    """
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save uploaded PDF
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run your full pipeline
    result = process_contract(file_path)

    return result
