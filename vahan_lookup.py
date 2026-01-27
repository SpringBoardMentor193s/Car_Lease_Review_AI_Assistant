import requests

url = "http://www.regcheck.org.uk/api/reg.asmx"
headers = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": "http://regcheck.org.uk/CheckIndia"
}

soap_body = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <CheckIndia xmlns="http://regcheck.org.uk">
      <RegistrationNumber>TN11AR6268</RegistrationNumber>
      <username>raghul</username>
    </CheckIndia>
  </soap:Body>
</soap:Envelope>"""

response = requests.post(url, data=soap_body, headers=headers)
print(response.text)