import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import tempfile

from services.text_extractor import extract_text_from_pdf, extract_vin_from_text
from services.vin_service import VINService
from services.ai_analyzer import AIAnalyzer
from models.schemas import AnalysisRequest

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "-k4")
ai_analyzer = AIAnalyzer(GEMINI_API_KEY)

@app.route("/")
def status():
    return {"status": "online", "version": "1.0.0"}

@app.route("/api/analyze-contract", methods=["POST"])
def analyze_contract():
    """Main endpoint for contract analysis."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    try:
        # 1. Save uploaded file
        pdf_file = request.files["file"]
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, pdf_file.filename)
        pdf_file.save(temp_path)
        
        # 2. Extract text from PDF
        contract_text = extract_text_from_pdf(temp_path)
        if not contract_text:
            return jsonify({
                "error": "This PDF contains no selectable text. Scanned PDFs are not supported."
            }), 400
        
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
        
        try:
            os.remove(temp_path)
        except:
            pass
        
        response = {
            "analysis": analysis_result.dict(),
            "metadata": {
                "vin_extracted": vin is not None,
                "vin": vin,
                "vehicle_details_fetched": vehicle_details is not None,
                "text_length": len(contract_text)
            }
        }
        
        if vehicle_details:
            response["vehicle_details"] = vehicle_details.dict()
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicle-details/<vin>", methods=["GET"])
def get_vehicle_details(vin: str):
    """Direct endpoint for vehicle details lookup."""
    if not VINService.validate_vin(vin):
        return jsonify({"error": "Invalid VIN format"}), 400
    
    try:
        vehicle_details = VINService.get_vehicle_details(vin)
        return jsonify(vehicle_details.dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)