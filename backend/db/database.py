import sqlite3
import json

DB_PATH = "backend/contracts.db"


# ---------- INIT DATABASE ----------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Main contract table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contract_text (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        extracted_text TEXT,
        sla_data TEXT,
        vehicle_data TEXT,
        recall_data TEXT,
        safety_rating TEXT,
        risk_data TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------- SAVE FUNCTIONS ----------

def save_contract(filename: str, extracted_text: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO contract_text (filename, extracted_text)
    VALUES (?, ?)
    """, (filename, extracted_text))

    contract_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return contract_id


def save_sla_data(contract_id: int, sla_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE contract_text
    SET sla_data = ?
    WHERE id = ?
    """, (json.dumps(sla_data), contract_id))

    conn.commit()
    conn.close()


def save_analysis_data(
    contract_id: int,
    vehicle_data: dict,
    recall_data: dict,
    safety_rating: dict | None,
    risk_data: dict
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE contract_text
    SET vehicle_data = ?,
        recall_data = ?,
        safety_rating = ?,
        risk_data = ?
    WHERE id = ?
    """, (
        json.dumps(vehicle_data),
        json.dumps(recall_data),
        json.dumps(safety_rating) if safety_rating else None,
        json.dumps(risk_data),
        contract_id
    ))

    conn.commit()
    conn.close()


# ---------- FETCH FOR NEGOTIATION ----------

def get_contract_analysis(contract_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT sla_data, vehicle_data, recall_data, safety_rating, risk_data
    FROM contract_text
    WHERE id = ?
    """, (contract_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "sla_data": json.loads(row[0]) if row[0] else {},
        "vehicle_data": json.loads(row[1]) if row[1] else {},
        "recall_data": json.loads(row[2]) if row[2] else {},
        "safety_rating": json.loads(row[3]) if row[3] else None,
        "risk_data": json.loads(row[4]) if row[4] else {}
    }
