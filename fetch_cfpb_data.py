import requests
import json

URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"

params = {
    "product": "Vehicle loan or lease",
    "has_narrative": "true",
    "size": 50
}

response = requests.get(URL, params=params)
data = response.json()

with open("data/complaints_raw.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("✅ CFPB complaint data saved")
