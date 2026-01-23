import requests

def decode_vin(vin: str) -> dict:
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    response = requests.get(url)
    data = response.json()["Results"]

    def get_value(name):
        for item in data:
            if item["Variable"] == name:
                return item["Value"]
        return None

    return {
        "vin": vin,
        "make": get_value("Make"),
        "model": get_value("Model"),
        "model_year": get_value("Model Year"),
        "body_class": get_value("Body Class"),
        "fuel_type": get_value("Fuel Type - Primary")
    }
