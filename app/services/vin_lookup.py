import requests

NHTSA_API_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"


def lookup_vehicle_by_vin(vin: str) -> dict:
    try:
        response = requests.get(NHTSA_API_URL.format(vin=vin), timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("Results", [])

        def get_value(key):
            for item in results:
                if item.get("Variable") == key:
                    return item.get("Value")
            return None

        return {
            "vin": vin,
            "make": get_value("Make"),
            "model": get_value("Model"),
            "model_year": get_value("Model Year"),
            "body_class": get_value("Body Class"),
            "fuel_type": get_value("Fuel Type - Primary"),
        }

    except Exception as e:
        return {
            "vin": vin,
            "error": str(e)
        }
