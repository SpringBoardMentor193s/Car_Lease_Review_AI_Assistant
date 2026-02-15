from flask import Flask, request, render_template, jsonify
import os

from ocr import extract_text
from services.llm_service import extract_sla
from services.vin_service import get_vehicle_details
from utils.clause_analysis import analyze_contract
from utils.price_estimator import estimate_vehicle_price

# CREATE APP
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# HOME ROUTE
@app.route("/")
def home():
    return "Car Lease AI Backend is Running"


# UPLOAD ROUTE
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file selected"

        file = request.files["file"]

        if file.filename == "":
            return "No file selected"

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        extracted_text = extract_text(file_path)
        analysis = analyze_contract(extracted_text)

        # temporary vehicle details
        make = "Toyota"
        model = "Camry"
        year = 2022

        market_price = estimate_vehicle_price(make, model, year)
        contract_price = 26000

        difference = contract_price - market_price

        if difference <= 0:
            fairness = "Excellent Deal ⭐⭐⭐⭐"
        elif difference < 2000:
            fairness = "Fair Deal ⭐⭐⭐"
        elif difference < 5000:
            fairness = "Slightly Expensive ⭐⭐"
        else:
            fairness = "Overpriced ❌"

        result = {
            "risk": analysis["risk"],
            "interest_rate": "7.5%",
            "tenure": "36 Months",
            "suggestions": analysis["suggestions"],
            "market_price": market_price,
            "contract_price": contract_price,
            "fairness": fairness
        }

        return render_template("dashboard.html", data=result)

    return render_template("upload.html")


# SLA API
@app.route("/extract-sla", methods=["POST"])
def extract_sla_api():
    text = request.json["text"]
    sla = extract_sla(text)
    return jsonify(sla)


# FULL ANALYSIS
@app.route("/full-analysis", methods=["POST"])
def full_analysis():
    text = request.json["text"]
    vin = request.json["vin"]

    sla = extract_sla(text)
    vehicle = get_vehicle_details(vin)

    return jsonify({
        "sla_details": sla,
        "vehicle_details": vehicle
    })


if __name__ == "__main__":
    app.run(debug=True)
