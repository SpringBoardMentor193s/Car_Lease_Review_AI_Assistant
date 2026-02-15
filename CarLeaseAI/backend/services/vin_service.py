
import requests

def get_vehicle_details(vin):
    """
    Fetch vehicle details using NHTSA VIN API
    """
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"
    response = requests.get(url)

    data = response.json()

    vehicle_info = {}

    for item in data["Results"]:
        if item["Variable"] in ["Make", "Model", "Model Year"]:
            vehicle_info[item["Variable"]] = item["Value"]

    return vehicle_info
