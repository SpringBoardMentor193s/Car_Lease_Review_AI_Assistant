from pathlib import Path
from typing import Dict, List, Optional

import json

from dotenv import load_dotenv
from flask import Flask, render_template, request

from .ocr_service import ocr_file
from .negotiation_service import build_payload, generate_negotiation_response
from .sla_extraction import extract_all
from .storage import save_ocr_text
from .vin_service import decode_vin, find_vin

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}

app = Flask(__name__)
load_dotenv(override=True)
load_dotenv(Path(__file__).resolve().parent.parent / ".env.example", override=True)

SLA_FIELD_MAP = [
    ("APR (%)", "apr_raw", "apr_percent"),
    ("Lease term (months)", "lease_term_raw", "lease_term_months"),
    ("Monthly payment", "monthly_payment_raw", "monthly_payment"),
    ("Down payment", "down_payment_raw", "down_payment"),
    ("Residual value", "residual_value_raw", "residual_value"),
    ("Mileage allowance", "mileage_raw", "mileage_per_year"),
    ("Mileage overage fee", "overage_raw", "overage_per_mile"),
    ("Buyout price", "buyout_raw", "buyout_price"),
]


def _render_home(
    message: Optional[str] = None,
    *,
    ocr_text: Optional[str] = None,
    filename: Optional[str] = None,
    storage_meta: Optional[Dict[str, str]] = None,
    sla_data: Optional[Dict] = None,
    debug_text: Optional[str] = None,
    vin_value: Optional[str] = None,
    vin_details: Optional[Dict[str, str]] = None,
    negotiation_response: Optional[str] = None,
    negotiation_payload: Optional[str] = None,
    negotiation_error: Optional[str] = None,
    negotiation_model: Optional[str] = None,
    negotiation_inputs: Optional[Dict[str, Optional[str]]] = None,
):
    sla_fields: List[Dict[str, Optional[str | float | int]]] = []
    if sla_data:
        for label, raw_key, value_key in SLA_FIELD_MAP:
            sla_fields.append(
                {
                    "label": label,
                    "raw": sla_data.get(raw_key),
                    "value": sla_data.get(value_key),
                }
            )

    sla_clauses = sla_data.get("clauses", {}) if sla_data else {}

    if negotiation_inputs is None:
        negotiation_inputs = {}
        if sla_data:
            mileage = sla_data.get("mileage_per_year")
            term = sla_data.get("lease_term_months")
            if mileage:
                negotiation_inputs["max_mileage_per_year"] = str(mileage)
            if term:
                negotiation_inputs["desired_term_months"] = str(term)

    return render_template(
        "index.html",
        message=message,
        ocr_text=ocr_text,
        filename=filename,
        storage_meta=storage_meta,
        sla_fields=sla_fields,
        sla_clauses=sla_clauses,
        debug_text=debug_text,
        vin_value=vin_value,
        vin_details=vin_details,
        negotiation_response=negotiation_response,
        negotiation_payload=negotiation_payload,
        negotiation_error=negotiation_error,
        negotiation_model=negotiation_model,
        negotiation_inputs=negotiation_inputs,
    )


@app.route("/", methods=["GET"])
def index():
    return _render_home()


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return _render_home(message="No file provided.")

    f = request.files["file"]
    if f.filename == "":
        return _render_home(message="Empty filename.")

    ext = Path(f.filename).suffix.lower()
    if ext not in ALLOWED:
        return _render_home(message=f"Unsupported file type: {ext}")

    out_path = UPLOAD_DIR / f.filename
    f.save(out_path)

    result = ocr_file(str(out_path))
    ocr_text = result.get("full_text") or ""

    saved_meta = save_ocr_text(f.filename, ocr_text)
    sla_data = extract_all(ocr_text) if ocr_text else {}
    detected_vin = find_vin(ocr_text)
    vin_details = decode_vin(detected_vin) if detected_vin else {}

    return _render_home(
        ocr_text=ocr_text,
        filename=f.filename,
        storage_meta=saved_meta,
        sla_data=sla_data,
        vin_value=detected_vin,
        vin_details=vin_details,
    )


@app.route("/debug-text", methods=["POST"])
def debug_text():
    uploaded = request.files.get("debug_file")
    if uploaded and uploaded.filename:
        custom_text = uploaded.stream.read().decode("utf-8", errors="ignore")
    else:
        custom_text = request.form.get("debug_text") or ""

    if not custom_text.strip():
        return _render_home(message="Provide text to debug.")

    sla_data = extract_all(custom_text)
    detected_vin = find_vin(custom_text)
    vin_details = decode_vin(detected_vin) if detected_vin else {}
    return _render_home(
        ocr_text=None,
        filename=None,
        storage_meta=None,
        sla_data=sla_data,
        debug_text=custom_text,
        vin_value=detected_vin,
        vin_details=vin_details,
    )


@app.route("/debug-vin", methods=["POST"])
def debug_vin():
    vin_input = (request.form.get("vin_input") or "").strip().upper()
    if not vin_input:
        return _render_home(message="Provide a VIN to decode.")
    if len(vin_input) != 17:
        return _render_home(message="VIN must be 17 characters.", vin_value=vin_input)

    vin_details = decode_vin(vin_input)
    return _render_home(
        vin_value=vin_input,
        vin_details=vin_details,
    )


@app.route("/negotiate", methods=["POST"])
def negotiate():
    source_text = request.form.get("source_text") or ""
    if not source_text.strip():
        return _render_home(message="Provide OCR or debug text before negotiating.")

    sla_data = extract_all(source_text)
    detected_vin = find_vin(source_text)
    vin_details = decode_vin(detected_vin) if detected_vin else {}

    negotiation_inputs = {
        "target_monthly_payment": request.form.get("target_monthly") or None,
        "target_due_at_signing": request.form.get("target_due") or None,
        "desired_term_months": request.form.get("target_term") or None,
        "max_mileage_per_year": request.form.get("target_mileage") or None,
        "location": request.form.get("location") or None,
        "priorities": request.form.get("priorities") or None,
        "extra_notes": request.form.get("notes") or None,
        "tone": request.form.get("tone") or None,
    }

    payload = build_payload(
        source_text=source_text,
        sla_data=sla_data,
        vin_value=detected_vin,
        vin_details=vin_details,
        user_goals=negotiation_inputs,
    )
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)

    response_text, error_message, model_used = generate_negotiation_response(payload)

    return _render_home(
        ocr_text=source_text,
        sla_data=sla_data,
        vin_value=detected_vin,
        vin_details=vin_details,
        negotiation_response=response_text,
        negotiation_payload=payload_json,
        negotiation_error=error_message,
        negotiation_model=model_used,
        negotiation_inputs=negotiation_inputs,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
