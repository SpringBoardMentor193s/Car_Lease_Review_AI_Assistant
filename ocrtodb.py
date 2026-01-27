import os
import psycopg2
import pytesseract
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Point to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT"),
    database=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
)
cur = conn.cursor()

# Image filename
filename = "vehicle.png"   # replace with your actual image file
img = Image.open(filename)

# Extract text using OCR
extracted_text = pytesseract.image_to_string(img)
print("Extracted text:\n", extracted_text)

# Insert into DB
cur.execute("""
    INSERT INTO contracts (filename, extracted_text)
    VALUES (%s, %s);
""", (filename, extracted_text))
conn.commit()
print(f"Inserted {filename} into contracts table.")

# Fetch all rows
cur.execute("SELECT * FROM contracts;")
rows = cur.fetchall()
print("\nAll contracts in DB:")
for row in rows:
    print(row)

cur.close()
conn.close()