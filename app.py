# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import io
import requests
from PIL import Image, UnidentifiedImageError
import pytesseract
from ocr_utils import extract_vin_or_reg_from_ocr, is_valid_vin
from backend.api.valuation import router as valuation_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lease-assistant")

app = FastAPI(title="Car Lease Review AI Assistant")

# include mocked valuation router (mounted at /api/valuation)
app.include_router(valuation_router, prefix="/api")


def decode_vin_nhtsa(vin: str) -> dict:
    """
    Decode VIN using NHTSA vPIC. Returns a dict with basic vehicle fields or empty dict on failure.
    """
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("NHTSA request failed for VIN %s: %s", vin, exc)
        return {}
    try:
        data = resp.json()
    except ValueError:
        return {}
    if "Results" in data and len(data["Results"]) > 0:
        r = data["Results"][0]
        return {
            "Make": r.get("Make") or "",
            "Model": r.get("Model") or "",
            "ModelYear": r.get("ModelYear") or "",
            "BodyClass": r.get("BodyClass") or "",
            "Manufacturer": r.get("Manufacturer") or ""
        }
    return {}


@app.get("/")
def root():
    return {"message": "Car Lease Review AI Assistant API is running"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts an image file (PNG/JPG) containing a lease or VIN.
    Runs OCR, extracts VIN, validates it, decodes via NHTSA and returns OCR + vehicle info.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Try to open as image
    try:
        image = Image.open(io.BytesIO(content))
    except UnidentifiedImageError:
        # If PIL cannot identify the image, return a helpful error
        raise HTTPException(status_code=400, detail="Uploaded file is not a supported image format")
    except Exception as exc:
        logger.exception("Failed to open uploaded file as image: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process uploaded file")

    # OCR
    try:
        text = pytesseract.image_to_string(image)
    except Exception as exc:
        logger.exception("Tesseract OCR failed: %s", exc)
        raise HTTPException(status_code=500, detail="OCR processing failed")

    # VIN extraction and validation
    vin = extract_vin_or_reg_from_ocr(text)
    if vin and is_valid_vin(vin):
        vehicle = decode_vin_nhtsa(vin)
        # NOTE: DB insertion disabled for now; enable when db_utils is ready
        # insert_contract_details(vin, text)
        return {
            "vin": vin,
            "status": "Detected (not saved to DB)",
            "vehicle": vehicle,
            "ocr_text": text
        }

    # No valid VIN found — return OCR text so user can inspect
    return {"error": "No valid VIN found", "ocr_text": text}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
