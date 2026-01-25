import json
from backend.ocr.ocr_service import extract_text_from_pdf
from backend.llm.contract_analyzer import extract_sla
from backend.db.database import save_contract_text, save_sla_data
from backend.pipeline.vin_enrichment import enrich_with_vehicle_data
from backend.pipeline.final_response import build_final_response

def process_contract(pdf_path: str):
    contract_text = extract_text_from_pdf(pdf_path)
    contract_id = save_contract_text(contract_text)

    sla_json = extract_sla(contract_text)

    # If the AI failed, sla_json will be a dict with an "error" key
    save_sla_data(contract_id, sla_json)

    # Step 5: Only enrich if we actually found a VIN
    if "VIN" in sla_json and sla_json["VIN"] not in [None, "null", "ERROR"]:
        vehicle_data = enrich_with_vehicle_data(sla_json)
    else:
        vehicle_data = {"warning": "VIN not available for verification"}

    return build_final_response(sla_json, vehicle_data)