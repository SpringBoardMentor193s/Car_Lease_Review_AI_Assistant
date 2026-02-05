import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from services.text_extractor import extract_text_from_pdf, extract_vin_from_text
from services.vin_service import VINService
from services.ai_analyzer import AIAnalyzer
from models.schemas import AnalysisRequest

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

ai_analyzer = AIAnalyzer(GEMINI_API_KEY)

@app.route("/")
def status():
    return {
        "status": "online",
        "version": "1.0.0",
        "milestone": "3 - MVP Backend Complete"
    }

@app.route("/api/analyze-contract", methods=["POST"])
def analyze_contract():
    """
    Milestone 1 & 2: Handles PDF upload, OCR, and SLA Extraction.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    try:
        pdf_file = request.files["file"]
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, pdf_file.filename)
        pdf_file.save(temp_path)
        
        contract_text = extract_text_from_pdf(temp_path)
        if not contract_text:
            return jsonify({"error": "No selectable text found in PDF."}), 400
        
        vin = extract_vin_from_text(contract_text)
        vehicle_details = None
        if vin and VINService.validate_vin(vin):
            try:
                vehicle_details = VINService.get_vehicle_details(vin)
            except Exception as e:
                app.logger.warning(f"VIN lookup failed: {str(e)}")
        
        analysis_request = AnalysisRequest(
            contract_text=contract_text,
            vehicle_details=vehicle_details
        )
        analysis_result = ai_analyzer.analyze_contract(analysis_request)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            "analysis": analysis_result.model_dump(),
            "metadata": {
                "vin": vin,
                "vehicle_details_fetched": vehicle_details is not None,
                "text_length": len(contract_text)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/negotiate", methods=["POST"])
def negotiate():
    """
    Milestone 3: AI-based negotiation chatbot for user guidance. 
    """
    data = request.json
    user_message = data.get("message")
    contract_context = data.get("contract_summary", "")
    history = data.get("history", []) 

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        model = ai_analyzer.model 
        chat = model.start_chat(history=history)
        
        system_instr = (
            f"You are a professional car lease negotiator. "
            f"Use this contract context to help the user: {contract_context}. "
            f"Suggest specific questions for the dealer and identify leverage points."
        )
        
        full_query = f"{system_instr}\n\nUser: {user_message}"
        response = chat.send_message(full_query)
        
        return jsonify({
            "reply": response.text,
            "history": history + [
                {"role": "user", "parts": [user_message]},
                {"role": "model", "parts": [response.text]}
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicle-details/<vin>", methods=["GET"])
def get_vehicle_details(vin: str):
    """Direct endpoint for manual VIN lookup."""
    if not VINService.validate_vin(vin):
        return jsonify({"error": "Invalid VIN format"}), 400
    
    try:
        vehicle_details = VINService.get_vehicle_details(vin)
        return jsonify(vehicle_details.dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)