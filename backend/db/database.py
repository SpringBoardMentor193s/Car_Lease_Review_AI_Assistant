import sqlite3

DB_PATH = "backend/contracts.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contract_text (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        extracted_text TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_contract(filename: str, extracted_text: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO contract_text (filename, extracted_text)
    VALUES (?, ?)
    """, (filename, extracted_text))

    conn.commit()
    conn.close()
