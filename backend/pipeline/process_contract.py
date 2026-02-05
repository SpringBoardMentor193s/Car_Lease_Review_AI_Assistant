from backend.ocr.ocr_service import extract_text_from_pdf
from backend.db.database import save_contract_text, save_sla_data
from backend.llm.contract_analyzer import extract_sla
from backend.app.services.nhtsa_service import decode_vin
from backend.pricing.price_estimator import estimate_price
from backend.scoring.fairness_score import calculate_fairness
from backend.llm.negotiation_chatbot import negotiation_chat


def process_contract(pdf_path: str):
    # 1.OCR
    contract_text = extract_text_from_pdf(pdf_path)

    # 2.Store raw contract text
    contract_id = save_contract_text(contract_text)

    # 3.SLA extraction (LLM)
    sla_data = extract_sla(contract_text)
    save_sla_data(contract_id, sla_data)

    # 4.VIN enrichment
    vehicle_data = None
    vin = sla_data.get("VIN")
    if vin:
        vehicle_data = decode_vin(vin)

    # 5.Market price estimation
    price_estimate = estimate_price(sla_data, vehicle_data)


    # 6. Fairness score calculation
    fairness = calculate_fairness(
        contract_sla=sla_data,
        price_estimate=price_estimate if price_estimate else {}
    )

    # 7.Negotiation chatbot (LLM)
    negotiation_advice = negotiation_chat(
        sla_data=sla_data,
        price_estimate=price_estimate,
        fairness_score=fairness["score"],
        user_message="Is this a good deal and how should I negotiate?"
    )

    # 8.Final response
    return {
        "status": "success",
        "contract_analysis": sla_data,
        "vehicle_details": vehicle_data,
        "price_estimation": price_estimate,
        "fairness": fairness,
        "negotiation_advice": negotiation_advice,
        "summary": {
            "monthly_payment": sla_data.get("Monthly Payment"),
            "fairness_score": fairness["score"]
        }
    }
