import sqlite3
import json  # Required to convert dict to string
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "car_lease.db"

def get_connection():
    """Create and return a SQLite DB connection"""
    return sqlite3.connect(DB_PATH)

def initialize_db():
    """Create required tables if they do not exist"""
    conn = get_connection()
    cursor = conn.cursor()

    # Contracts table (OCR text)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_text TEXT NOT NULL
        )
    """)

    # SLA extracted data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sla_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            sla_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts (id)
        )
    """)

    conn.commit()
    conn.close()

def save_contract_text(contract_text: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO contracts (contract_text) VALUES (?)",
        (contract_text,)
    )

    conn.commit()
    contract_id = cursor.lastrowid
    conn.close()

    return contract_id

def save_sla_data(contract_id: int, sla_data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    # FIX: Convert the dictionary to a JSON string for SQLite storage
    sla_json_str = json.dumps(sla_data)

    cursor.execute(
        """
        INSERT INTO sla_data (contract_id, sla_json)
        VALUES (?, ?)
        """,
        (contract_id, sla_json_str)
    )

    conn.commit()
    conn.close()