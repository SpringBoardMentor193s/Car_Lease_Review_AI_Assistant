import sqlite3

def get_contract_text(contract_id):
    conn = sqlite3.connect("backend/contracts.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT extracted_text FROM contract_text WHERE id = ?",
        (contract_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None
