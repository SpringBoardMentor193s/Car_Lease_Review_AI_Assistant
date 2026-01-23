from fastapi import APIRouter, HTTPException, Body
from app.services.sla_extractor import extract_sla_rule_based
from app.services.llm_sla_extractor import extract_sla_llm_based
from app.services.vin_lookup import lookup_vehicle_by_vin
from app.database import get_db_connection
import json

router = APIRouter()


@router.get("/")
def get_all_contracts():
    conn = get_db_connection()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT
            contract_id,
            original_filename,
            text_length,
            status,
            created_at
        FROM contracts
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return [
        {
            "contract_id": row["contract_id"],
            "original_filename": row["original_filename"],
            "text_length": row["text_length"],
            "status": row["status"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


@router.get("/{contract_id}")
def get_contract_by_id(contract_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT
            contract_id,
            original_filename,
            extracted_text,
            text_length,
            status,
            created_at,
            vin,
            sla_json,
            vehicle_json
        FROM contracts
        WHERE contract_id = ?
    """, (contract_id,)).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {
        "contract_id": row["contract_id"],
        "original_filename": row["original_filename"],
        "extracted_text": row["extracted_text"],
        "text_length": row["text_length"],
        "status": row["status"],
        "created_at": row["created_at"],
        "vin": row["vin"],
        "sla_json": json.loads(row["sla_json"]) if row["sla_json"] else None,
        "vehicle_json": json.loads(row["vehicle_json"]) if row["vehicle_json"] else None
    }


@router.delete("/{contract_id}/delete")
def delete_contract(contract_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT id FROM contracts WHERE contract_id = ?",
        (contract_id,)
    ).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    cursor.execute(
        "DELETE FROM contracts WHERE contract_id = ?",
        (contract_id,)
    )

    conn.commit()
    conn.close()

    return {
        "contract_id": contract_id,
        "status": "deleted"
    }


@router.get("/{contract_id}/analyze")
def analyze_contract(contract_id: str, mode: str = "rule"):
    """
    mode = rule | llm | hybrid
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT extracted_text, vin
        FROM contracts
        WHERE contract_id = ?
    """, (contract_id,)).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    text = row["extracted_text"]
    vin = row["vin"]

    # ---------- SLA Extraction ----------
    if mode == "llm":
        sla = extract_sla_llm_based(text)
    elif mode == "hybrid":
        sla = extract_sla_llm_based(text) or extract_sla_rule_based(text)
    else:
        sla = extract_sla_rule_based(text)

    # Normalize SLA to dict
    if hasattr(sla, "dict"):
        sla_dict = sla.dict()
    elif isinstance(sla, dict):
        sla_dict = sla
    else:
        sla_dict = {}

    # ---------- VIN Lookup ----------
    vehicle = None
    if vin:
        vehicle = lookup_vehicle_by_vin(vin)

    # ---------- Save to DB ----------
    cursor.execute("""
        UPDATE contracts
        SET sla_json = ?, vehicle_json = ?
        WHERE contract_id = ?
    """, (
        json.dumps(sla_dict),
        json.dumps(vehicle) if vehicle else None,
        contract_id
    ))

    conn.commit()
    conn.close()

    return {
        "contract_id": contract_id,
        "analysis_type": mode,
        "sla": sla_dict,
        "vehicle": vehicle
    }


@router.post("/{contract_id}/vin")
def update_contract_vin(contract_id: str, vin: str = Body(..., embed=True)):
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT id FROM contracts WHERE contract_id = ?",
        (contract_id,)
    ).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    cursor.execute(
        "UPDATE contracts SET vin = ? WHERE contract_id = ?",
        (vin, contract_id)
    )

    conn.commit()
    conn.close()

    return {
        "contract_id": contract_id,
        "vin": vin,
        "status": "VIN updated successfully"
    }

@router.get("/vin/{vin}")
def get_vehicle_by_vin(vin: str):
    vehicle = lookup_vehicle_by_vin(vin)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    return vehicle
