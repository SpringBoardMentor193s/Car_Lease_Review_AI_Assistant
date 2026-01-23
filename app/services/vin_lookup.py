import requests
from typing import Optional, Dict

NHTSA_API_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"


def lookup_vehicle_by_vin(vin: str) -> Optional[Dict]:
    """
    Lookup vehicle details using NHTSA vPIC VIN decoder API
    """

    if not vin:
        return None

    try:
        response = requests.get(
            NHTSA_API_URL.format(vin=vin),
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("Results", [])

        def get_value(variable_name: str):
            for item in results:
                if item.get("Variable") == variable_name:
                    return item.get("Value")
            return None

        # Normalize missing values to avoid null confusion
        return {
            "vin": vin,
            "make": get_value("Make") or "Unknown",
            "model": get_value("Model") or "Unknown",
            "model_year": get_value("Model Year"),
            "body_class": get_value("Body Class") or "Unknown",
            "fuel_type": get_value("Fuel Type - Primary") or "Unknown",
        }

    except Exception as e:
        # Fail gracefully (important for project stability)
        return {
            "vin": vin,
            "error": str(e)
        }
