import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT"),
    database=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
)
cur = conn.cursor()

# Print current database
cur.execute("SELECT current_database();")
print("Connected to DB:", cur.fetchone()[0])

# Create contracts table if not exists
cur.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        extracted_text TEXT
    );
""")
conn.commit()
print("Table 'contracts' is ready.")

# Show all tables in public schema
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public';
""")
print("Tables in 'public':", [r[0] for r in cur.fetchall()])

cur.close()
conn.close()
print("Connection closed.")