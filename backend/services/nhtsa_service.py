import requests

def get_vehicle_details_from_vin(vin: str):
    if not vin:
        return None

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json().get("Results", [])

    vehicle_info = {}
    for item in data:
        if item["Variable"] in ["Make", "Model", "Model Year"]:
            vehicle_info[item["Variable"]] = item["Value"]

    return vehicle_info
