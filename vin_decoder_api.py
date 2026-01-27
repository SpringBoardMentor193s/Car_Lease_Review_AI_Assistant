import requests

def decode_vin(vin: str) -> dict:
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        result = data.get("Results", [{}])[0]
        if result.get("ErrorCode") == "0":
            return result
        else:
            print("⚠️ VIN decode error:", result.get("ErrorText"))
            return None
    else:
        print("❌ API request failed:", response.status_code)
        return None