import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.database import get_db_connection
from app.services.ocr import extract_text

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_MB = 10

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "storage" / "raw_contracts"
TEXT_DIR = BASE_DIR / "storage" / "ocr_text"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    # 1️⃣ Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, JPEG, PNG files are allowed"
        )

    # 2️⃣ Read file bytes safely (CRITICAL FIX)
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )

    # 3️⃣ Save file
    contract_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{contract_id}{ext}"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 4️⃣ OCR extraction
    extracted_text = extract_text(file_path)
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO contracts (
            contract_id,
            original_filename,
            extracted_text,
            text_length,
            status
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        contract_id,
        file.filename,
        extracted_text,
        len(extracted_text),
        "processed"
    ))

    conn.commit()
    conn.close()


    # 5️⃣ Save OCR text
    text_file = TEXT_DIR / f"{contract_id}.txt"
    text_file.write_text(extracted_text, encoding="utf-8")

    # 6️⃣ Response
    return {
        "contract_id": contract_id,
        "original_filename": file.filename,
        "status": "processed",
        "text_length": len(extracted_text)
    }
