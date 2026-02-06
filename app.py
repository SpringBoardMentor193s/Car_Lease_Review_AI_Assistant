from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import requests
import os
from openai import OpenAI, RateLimitError

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ================= CONFIG =================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r"C:\Users\Neha\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

ENABLE_LLM = True  # set False if no OpenAI credits

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================

app = FastAPI(title="Car Contract Review AI", version="2.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "API running"}

# ================= VIN API =================

def get_vin_data(vin: str):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    res = requests.get(url).json()

    data = {}
    for item in res["Results"]:
        if item["Variable"] in ["Make", "Model", "Model Year", "Body Class"]:
            data[item["Variable"]] = item["Value"]

    recall_url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?vin={vin}"
    recalls = requests.get(recall_url).json()
    data["Recalls"] = recalls.get("results", [])

    return data

# ================= OCR =================

def extract_text_from_pdf(pdf_path: str):
    text = ""

    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()

    if len(text.strip()) < 50:
        images = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=POPPLER_PATH
        )
        for img in images:
            text += pytesseract.image_to_string(img)

    return text.strip()

# ================= CLAUSE EXTRACTION =================

def extract_clauses(text: str):
    clauses = {
        "fees": [],
        "penalties": [],
        "mileage": [],
        "termination": []
    }

    for line in text.split("\n"):
        l = line.lower()

        if any(k in l for k in ["fee", "charge", "amount"]):
            clauses["fees"].append(line)

        if any(k in l for k in ["penalty", "fine", "late"]):
            clauses["penalties"].append(line)

        if any(k in l for k in ["mileage", "km", "odometer"]):
            clauses["mileage"].append(line)

        if any(k in l for k in ["terminate", "termination", "cancel"]):
            clauses["termination"].append(line)

    return clauses

# ================= RISK FLAGS =================

def detect_risks(clauses):
    risks = []

    if len(clauses["fees"]) > 5:
        risks.append("Multiple fees detected (possible hidden charges)")

    if clauses["penalties"]:
        risks.append("Penalty clauses present")

    if not clauses["termination"]:
        risks.append("Termination clause missing")

    return risks

# ================= RISK SCORE =================

def calculate_risk_score(text: str):
    high = ["penalty", "termination", "non-refundable", "lawsuit", "forfeit"]
    medium = ["late fee", "interest", "liability", "maintenance"]
    low = ["warranty", "inspection", "service"]

    score = 0
    found = []

    t = text.lower()

    for w in high:
        if w in t:
            score += 3
            found.append({"clause": w, "severity": "High"})

    for w in medium:
        if w in t:
            score += 2
            found.append({"clause": w, "severity": "Medium"})

    for w in low:
        if w in t:
            score += 1
            found.append({"clause": w, "severity": "Low"})

    level = "Low"
    if score >= 8:
        level = "High"
    elif score >= 4:
        level = "Medium"

    return {
        "risk_score": score,
        "risk_level": level,
        "risky_clauses_found": found
    }

# ================= GPT SUMMARY =================

def gpt_summary(contract_text: str, risk_analysis: dict):
    if not ENABLE_LLM:
        return "LLM disabled"

    try:
        prompt = f"""
Explain this car contract in simple language.

Focus on:
- Legal risks
- Penalties
- Termination
- Hidden charges

Risk Level: {risk_analysis['risk_level']}
Risk Score: {risk_analysis['risk_score']}

Contract:
{contract_text[:3000]}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content

    except RateLimitError:
        return "GPT explanation unavailable (quota exceeded)."

    except Exception as e:
        return f"GPT error: {str(e)}"

# ================= PDF REPORT =================

def generate_report(vin, clauses, risks, summary, risk_analysis):
    file_name = f"contract_report_{vin}.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_name)

    content = []

    content.append(Paragraph(f"Car Contract Report – {vin}", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(
        f"Risk Level: {risk_analysis['risk_level']} (Score {risk_analysis['risk_score']})",
        styles["BodyText"]
    ))

    content.append(Spacer(1, 12))

    content.append(Paragraph("Risk Flags", styles["Heading2"]))
    for r in risks:
        content.append(Paragraph(r, styles["BodyText"]))

    content.append(Spacer(1, 12))
    content.append(Paragraph("Key Clauses", styles["Heading2"]))

    for k, v in clauses.items():
        content.append(Paragraph(k.upper(), styles["Heading3"]))
        for line in v[:5]:
            content.append(Paragraph(line, styles["BodyText"]))

    content.append(Spacer(1, 12))
    content.append(Paragraph("AI Summary", styles["Heading2"]))
    content.append(Paragraph(summary, styles["BodyText"]))

    doc.build(content)
    return file_name

# ================= MAIN API =================

@app.post("/analyze-contract")
async def analyze_contract(
    vin: str = Form(...),
    file: UploadFile = File(...)
):
    if len(vin) != 17:
        return {"error": "VIN must be 17 characters"}

    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF allowed"}

    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    text = extract_text_from_pdf(temp_path)
    vin_data = get_vin_data(vin)
    clauses = extract_clauses(text)
    risks = detect_risks(clauses)
    risk_analysis = calculate_risk_score(text)
    summary = gpt_summary(text, risk_analysis)
    report = generate_report(vin, clauses, risks, summary, risk_analysis)

    os.remove(temp_path)

    return {
        "vin": vin,
        "vehicle_details": vin_data,
        "clauses": clauses,
        "risk_flags": risks,
        "risk_analysis": risk_analysis,
        "llm_summary": summary,
        "report": report,
        "status": "analysis complete"
    }
