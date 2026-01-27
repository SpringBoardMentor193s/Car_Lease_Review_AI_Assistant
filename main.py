from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2

from vin_decoder_api import decode_vin
from ocr_reader import ocr_from_image, ocr_from_pdf
from ocr_utils import extract_vin_or_reg_from_ocr, is_valid_vin
from vin_utils import clean_vin, is_plausible_vin
from llm_extractor import extract_sla_terms   # GPT call


# ---------------- VIN parsing ----------------
def parse_vin_details(details: dict) -> dict:
    if not details:
        return {}
    return {
        "Make": details.get("Make"),
        "Model": details.get("Model"),
        "FuelType": details.get("FuelTypePrimary"),
        "EngineSize": details.get("EngineCylinders"),
        "RegistrationYear": details.get("ModelYear"),
    }


def insert_vehicle_into_postgres(conn, reg_no, make, model, fuel_type, engine_size, registration_year):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vehicle_details (reg_no, make, model, fuel_type, engine_size, registration_year)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (reg_no) DO UPDATE
            SET make = EXCLUDED.make,
                model = EXCLUDED.model,
                fuel_type = EXCLUDED.fuel_type,
                engine_size = EXCLUDED.engine_size,
                registration_year = EXCLUDED.registration_year;
            """,
            (reg_no, make, model, fuel_type, engine_size, registration_year)
        )
        conn.commit()
    print("✅ Vehicle details inserted into PostgreSQL successfully!")


# ---------------- SLA parsing ----------------
def safe_int(value):
    if not value:
        return None
    cleaned = str(value).replace(",", "").replace(" ", "").strip()
    return int(cleaned) if cleaned.isdigit() else None

def insert_sla_into_postgres(sla: dict, contract_id=None):
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO contract_sla (
          contract_id, apr_percent, term_months, monthly_payment, down_payment,
          residual_value, mileage_allowance_yr, mileage_overage_fee,
          early_termination_fee, purchase_option_price, insurance_requirements,
          maintenance_resp, warranty_summary, late_fee_policy, other_terms
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        contract_id,
        sla.get("APR"),
        safe_int(sla.get("TermMonths")),
        sla.get("MonthlyPayment"),
        sla.get("DownPayment"),
        sla.get("ResidualValue"),
        safe_int(sla.get("MileageAllowancePerYear")),
        sla.get("MileageOverageFee"),
        sla.get("EarlyTerminationFee"),
        sla.get("PurchaseOptionPrice"),
        sla.get("InsuranceRequirements"),
        sla.get("MaintenanceResponsibilities"),
        sla.get("WarrantySummary"),
        sla.get("LateFeePolicy"),
        sla.get("OtherTerms")
    ))
    conn.commit()
    cur.close()
    conn.close()
    print("✅ SLA inserted into PostgreSQL successfully!")


# ---------------- Main pipeline ----------------
def process_file(conn, file_path: str):
    # OCR extraction
    if file_path.lower().endswith(".pdf"):
        ocr_text = ocr_from_pdf(file_path)
    else:
        # Use OCR.Space for images
        from ocr_api import ocr_space_image
        ocr_text = ocr_space_image(file_path)

    print("🔍 OCR text:\n", ocr_text)

    # GPT SLA extraction
    sla_data = extract_sla_terms(ocr_text)
    print("Parsed SLA from GPT:", sla_data)
    insert_sla_into_postgres(sla_data, contract_id=None)

    # VIN extraction + cleanup
    vin_raw = extract_vin_or_reg_from_ocr(ocr_text)
    vin = clean_vin(vin_raw)
    if not vin or not is_plausible_vin(vin):
        print(f"⚠️ No valid VIN found: {vin_raw}")
        print("🔍 OCR text for debugging:\n", ocr_text)
        return None, None

    print("Detected VIN:", vin)
    vehicle_details = decode_vin(vin)
    parsed = parse_vin_details(vehicle_details)
    print("Parsed VIN Details:", parsed)

    insert_vehicle_into_postgres(
        conn,
        vin,
        parsed.get("Make"),
        parsed.get("Model"),
        parsed.get("FuelType"),
        parsed.get("EngineSize"),
        parsed.get("RegistrationYear")
    )

    return vin, parsed


def fetch_all_vehicles():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    cur = conn.cursor()
    cur.execute("SELECT reg_no, make, model, fuel_type, engine_size, registration_year, created_at FROM vehicle_details")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print("📋 Vehicles in DB:", rows)


def fetch_all_slas():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM contract_sla")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print("📋 SLA rows in DB:", rows)


# ---------------- Entry point ----------------
if __name__ == "__main__":
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    process_file(conn, "samplelease.png")
    fetch_all_vehicles()
    fetch_all_slas()   # 👈 Now you’ll see SLA rows too
    conn.close()