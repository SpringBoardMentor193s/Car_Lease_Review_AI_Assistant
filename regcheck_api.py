# regcheck_api.py
import os
import requests
import xml.etree.ElementTree as ET
import json

REGCHECK_URL = "http://www.regcheck.org.uk/api/reg.asmx"
HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": "http://regcheck.org.uk/CheckIndia"
}

API_USERNAME = os.getenv("REGCHECK_USERNAME")  # set this in your .env

def build_soap_body(registration_number: str, username: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <CheckIndia xmlns="http://regcheck.org.uk">
      <RegistrationNumber>{registration_number}</RegistrationNumber>
      <username>{username}</username>
    </CheckIndia>
  </soap:Body>
</soap:Envelope>"""

def call_regcheck(registration_number: str) -> dict:
    if not API_USERNAME:
        raise ValueError("REGCHECK_USERNAME not set. Add it to your .env")

    soap_body = build_soap_body(registration_number, API_USERNAME)
    resp = requests.post(REGCHECK_URL, data=soap_body, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    # Parse XML to extract <vehicleJson>
    root = ET.fromstring(resp.text)
    ns = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "ns": "http://regcheck.org.uk"
    }
    vehicle_json_el = root.find(".//ns:vehicleJson", ns)
    if vehicle_json_el is None or not vehicle_json_el.text:
        raise ValueError("vehicleJson not found in response")

    try:
        vehicle = json.loads(vehicle_json_el.text)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse vehicleJson")

    return vehicle