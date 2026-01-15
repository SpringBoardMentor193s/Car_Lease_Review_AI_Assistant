import sqlite3
import json

DB_PATH = "backend/contracts.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contract_text (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        extracted_text TEXT,
        sla_data TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_contract(filename: str, extracted_text: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO contract_text (filename, extracted_text)
    VALUES (?, ?)
    """, (filename, extracted_text))

    contract_id = cursor.lastrowid  # 🔑 IMPORTANT

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
