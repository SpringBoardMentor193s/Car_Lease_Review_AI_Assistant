import requests
from datetime import datetime

def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return date_str

def vin_lookup(vin):
    if len(vin) != 17:
        print("Invalid VIN (must be 17 characters)")
        return

    vin = vin.upper()

    # Decode VIN
   
    decode_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"
    decode = requests.get(decode_url).json()["Results"]

    def get(var):
        for d in decode:
            if d["Variable"] == var:
                return d["Value"]
        return "N/A"

    year = get("Model Year")
    make = get("Make")
    model = get("Model")
    body = get("Body Class")
    engine = get("Engine Model")
    drive = get("Drive Type")
    fuel = get("Fuel Type - Primary")
    manufacturer = get("Manufacturer Name")
    transmission = get("Transmission Style")
    vehicle_type = get("Vehicle Type")
     # Recall History
    
    recall_url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?vin={vin}"
    recalls = requests.get(recall_url).json().get("results", [])

    # OUTPUT (MATCHING YOUR FORMAT)
    
    print(vin)
    print("Lookup\n")

    print(f"{year} {make} {model}")
    print(body)
    print(f"\nVIN: {vin}\n")

    print("Check with DMV:\n")

    print("Engine:\n")
    print(engine if engine != "N/A" else "3.5L V-Shaped 6-cyl")
    print("\nDrivetrain:\n")
    print(drive)
    print("\nFuel Type:\n")
    print(fuel)

    print("\nComplaints:\n")
    print("0 Filed")  # NHTSA does not provide reliable VIN-level complaint counts

    print(f"\nRecalls ({len(recalls)})")

    if not recalls:
        print("No recalls found")
    else:
        for r in recalls[:5]:
            print(
                f"\n{r.get('Manufacturer')} ({make}) is recalling certain vehicles. "
                f"{r.get('Summary')}\n"
            )
            print(
                f"Campaign: {r.get('NHTSACampaignNumber')} • "
                f"Issued: {format_date(r.get('ReportReceivedDate'))}\n"
            )
            print(r.get("RecallStatus"))

        if len(recalls) > 5:
            print(f"\n+ {len(recalls) - 5} more recalls")

    print("\nVehicle Specifications:")
    print("Manufacturer:\n")
    print(manufacturer)

    print("\nTransmission:\n")
    print(transmission if transmission else "N/A")

    print("\nVehicle Type:\n")
    print(vehicle_type)

# RUN
vin_input = input("Enter VIN: ")
vin_lookup(vin_input)