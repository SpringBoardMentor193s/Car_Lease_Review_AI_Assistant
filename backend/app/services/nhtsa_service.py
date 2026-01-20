import requests
import re

VIN_REGEX = r"^[A-HJ-NPR-Z0-9]{17}$"

def is_valid_vin(vin: str) -> bool:
    return bool(re.match(VIN_REGEX, vin))


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

    return {
        "VIN": vin,
        "Make": result.get("Make"),
        "Model": result.get("Model"),
        "ModelYear": result.get("ModelYear"),
        "BodyClass": result.get("BodyClass"),
        "FuelType": result.get("FuelTypePrimary"),
        "PlantCountry": result.get("PlantCountry"),
    }
