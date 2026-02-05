import requests  # type: ignore[import]


def lookup_vin(vin):
    url = (
        "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/"
        f"{vin}?format=json"
    )
    data = requests.get(url).json()

    result = {}
    for item in data["Results"]:
        if item["Value"]:
            result[item["Variable"]] = item["Value"]

    return {
        "make": result.get("Make"),
        "model": result.get("Model"),
        "year": result.get("Model Year"),
        "body_class": result.get("Body Class")
    }
