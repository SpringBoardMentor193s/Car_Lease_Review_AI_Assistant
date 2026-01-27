import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT"),   # now 5555
    database=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
)
cur = conn.cursor()

# Insert a sample row
filename = "sample-contract-01.png"
extracted_text = "This is a dummy contract text for testing DB flow."
cur.execute("""
    INSERT INTO contracts (filename, extracted_text)
    VALUES (%s, %s);
""", (filename, extracted_text))
conn.commit()
print("Inserted:", filename)

# Fetch all rows
cur.execute("SELECT * FROM contracts;")
rows = cur.fetchall()
print("\nAll contracts:")
for row in rows:
    print(row)

cur.close()
conn.close()