from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from pydantic import BaseModel

from backend.ocr.ocr_utils import extract_text_from_pdf
from backend.db.database import (
    init_db,
    save_contract,
    save_sla_data,
    save_analysis_data,
    get_contract_analysis
)

from backend.extraction.rule_extractor import extract_sla_fields
from backend.extraction.llm_extractor import extract_sla_with_llm
from backend.extraction.vin_extractor import extract_vin

from backend.services.nhtsa_service import (
    get_vehicle_details_from_vin,
    get_vehicle_recalls,
    get_vehicle_safety_rating
)

from backend.analysis.risk_engine import calculate_lease_risk
from backend.analysis.advisor import generate_lease_advice
from backend.analysis.summary_engine import generate_contract_summary
from backend.analysis.negotiator import negotiate_with_user


app = FastAPI()

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

init_db()

# -------------------- UPLOAD CONTRACT ENDPOINT -------------------- #

@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # 1️⃣ Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2️⃣ OCR
    extracted_text = extract_text_from_pdf(file_path)

    # 3️⃣ Save contract
    contract_id = save_contract(file.filename, extracted_text)

    # 4️⃣ SLA extraction
    rule_sla = extract_sla_fields(extracted_text)
    llm_sla = extract_sla_with_llm(extracted_text)

    # 5️⃣ Merge SLA (RULE > LLM)
    final_sla = {}
    for key in rule_sla:
        final_sla[key] = rule_sla[key] if rule_sla[key] is not None else llm_sla.get(key)

    save_sla_data(contract_id, final_sla)

    # 6️⃣ VIN extraction
    vin = extract_vin(extracted_text)

    # 7️⃣ Vehicle data
    vehicle_data = get_vehicle_details_from_vin(vin)

    # 8️⃣ Recall data
    recall_data = get_vehicle_recalls(vin, vehicle_data)

    # 9️⃣ Safety rating
    safety_rating = get_vehicle_safety_rating(
        vehicle_data.get("Make"),
        vehicle_data.get("Model"),
        vehicle_data.get("Model Year")
    )

    # 🔟 Risk assessment
    risk_assessment = calculate_lease_risk(
        final_sla,
        vehicle_data,
        recall_data,
        safety_rating
    )

    # 1️⃣1️⃣ Summary
    contract_summary = generate_contract_summary(
        final_sla,
        vehicle_data,
        recall_data,
        risk_assessment
    )

    # 1️⃣2️⃣ Advisory
    ai_advice = generate_lease_advice(risk_assessment)

    # 🔥 SAVE FULL ANALYSIS FOR FUTURE NEGOTIATION
    save_analysis_data(
        contract_id,
        vehicle_data,
        recall_data,
        safety_rating,
        risk_assessment
    )

    # ✅ FINAL RESPONSE
    return {
        "message": "File uploaded and fully analyzed",
        "contract_id": contract_id,
        "file_name": file.filename,
        "vin": vin,
        "vehicle_data": vehicle_data,
        "recall_data": recall_data,
        "sla_data": final_sla,
        "risk_assessment": risk_assessment,
        "ai_advice": ai_advice,
        "contract_summary": contract_summary,
        "safety_rating": safety_rating,
        "preview": extracted_text[:500],
    }


# -------------------- NEGOTIATION CHAT ENDPOINT -------------------- #

class NegotiationRequest(BaseModel):
    contract_id: int
    user_message: str


@app.post("/negotiate")
async def negotiate(request: NegotiationRequest):

    # 🔹 Load all stored analysis automatically
    data = get_contract_analysis(request.contract_id)

    if not data:
        raise HTTPException(status_code=404, detail="Contract not found")

    reply = negotiate_with_user(
        request.user_message,
        data["sla_data"],
        data["risk_data"],
        data["vehicle_data"]
    )

    return {
        "contract_id": request.contract_id,
        "user_message": request.user_message,
        "assistant_reply": reply
    }
