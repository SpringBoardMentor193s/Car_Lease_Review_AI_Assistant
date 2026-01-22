import requests
import re
import sqlite3
from pathlib import Path

VIN_REGEX = r"^[A-HJ-NPR-Z0-9]{17}$"

# Path to SQLite DB file
DB_PATH = Path(__file__).parents[2] / "db" / "car_lease.db"

def is_valid_vin(vin: str) -> bool:
    return bool(re.match(VIN_REGEX, vin))
def save_vehicle_data(vehicle: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO vehicle_data (
        vin, make, model, model_year, body_class, fuel_type, plant_country
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        vehicle["VIN"],
        vehicle["Make"],
        vehicle["Model"],
        vehicle["ModelYear"],
        vehicle["BodyClass"],
        vehicle["FuelType"],
        vehicle["PlantCountry"],
    ))

    conn.commit()
    conn.close()


import requests
import re
import sqlite3
from pathlib import Path

VIN_REGEX = r"^[A-HJ-NPR-Z0-9]{17}$"

# Path to SQLite DB file
DB_PATH = Path(__file__).parents[2] / "db" / "car_lease.db"

def is_valid_vin(vin: str) -> bool:
    return bool(re.match(VIN_REGEX, vin))
def save_vehicle_data(vehicle: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO vehicle_data (
        vin, make, model, model_year, body_class, fuel_type, plant_country
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        vehicle["VIN"],
        vehicle["Make"],
        vehicle["Model"],
        vehicle["ModelYear"],
        vehicle["BodyClass"],
        vehicle["FuelType"],
        vehicle["PlantCountry"],
    ))

    conn.commit()
    conn.close()


def decode_vin(vin: str) -> dict:
    """
    Decode VIN using NHTSA public API and return key vehicle details.
    """
    if not is_valid_vin(vin):
        raise ValueError("Invalid VIN format")

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    result = response.json()["Results"][0]

    vehicle = {
    "VIN": vin,
    "Make": result.get("Make"),
    "Model": result.get("Model"),
    "ModelYear": result.get("ModelYear"),
    "BodyClass": result.get("BodyClass"),
    "FuelType": result.get("FuelTypePrimary"),
    "PlantCountry": result.get("PlantCountry"),
}

    save_vehicle_data(vehicle)
    return vehicle


import sqlite3

conn = sqlite3.connect("backend/db/car_lease.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM vehicle_data")
rows = cursor.fetchall()

rows
