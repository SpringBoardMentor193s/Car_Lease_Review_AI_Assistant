# services/nhtsa_service.py

import requests
import json
import os
from typing import Dict, List, Optional

# Path to store vehicle JSON files
VEHICLE_DATA_PATH = "vehicle_data"  # relative to backend folder

def fetch_vehicle_data(vin: str) -> Dict:
    """
    Fetch vehicle details from NHTSA API using VIN,
    save JSON as <VIN>_vin.json in vehicle_data folder,
    and return the data as dict.
    """
    vin = vin.upper().strip()  # ensure VIN format is consistent
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"

    # Call NHTSA API
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch VIN data: {response.status_code}")

    data = response.json()

    # Extract useful info (all non-empty fields)
    vehicle_info = {}
    for item in data.get("Results", []):
        key = item.get("Variable")
        value = item.get("Value")
        if key and value:
            vehicle_info[key] = value

    # Ensure folder exists
    os.makedirs(VEHICLE_DATA_PATH, exist_ok=True)

    # File name: <VIN>_vin.json
    file_path = os.path.join(VEHICLE_DATA_PATH, f"{vin}_vin.json")
    with open(file_path, "w") as f:
        json.dump(vehicle_info, f, indent=4)

    return vehicle_info


def fetch_vehicle_recalls(vin: str) -> List[Dict]:
    """
    Fetch vehicle recall information from NHTSA Recalls API.
    
    Args:
        vin: Vehicle Identification Number
        
    Returns:
        List of recall dictionaries containing:
        - NHTSACampaignNumber: Recall campaign ID
        - Component: Affected component
        - Summary: Description of the issue
        - Consequence: Potential consequences
        - Remedy: How to fix the issue
        - Notes: Additional information
        - ReportReceivedDate: When recall was reported
    """
    vin = vin.upper().strip()
    url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?make=&model=&year=&vin={vin}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Warning: NHTSA Recalls API returned status {response.status_code}")
            return []
        
        data = response.json()
        recalls = data.get("results", [])
        
        # Save recalls to file for reference
        if recalls:
            os.makedirs(VEHICLE_DATA_PATH, exist_ok=True)
            recalls_file = os.path.join(VEHICLE_DATA_PATH, f"{vin}_recalls.json")
            with open(recalls_file, "w") as f:
                json.dump(recalls, f, indent=4)
        
        return recalls
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recalls: {str(e)}")
        return []


def fetch_complete_vehicle_data(vin: str) -> Dict:
    """
    Fetch complete vehicle data including specifications and recalls.
    
    Args:
        vin: Vehicle Identification Number
        
    Returns:
        Dictionary containing:
        - vehicle_info: Vehicle specifications from decode VIN API
        - recalls: List of recall information
        - recall_count: Number of active recalls
    """
    vin = vin.upper().strip()
    
    # Fetch vehicle specifications
    vehicle_info = fetch_vehicle_data(vin)
    
    # Fetch recalls
    recalls = fetch_vehicle_recalls(vin)
    
    # Combine data
    complete_data = {
        "vin": vin,
        "vehicle_info": vehicle_info,
        "recalls": recalls,
        "recall_count": len(recalls),
        "has_recalls": len(recalls) > 0
    }
    
    # Save complete data
    os.makedirs(VEHICLE_DATA_PATH, exist_ok=True)
    complete_file = os.path.join(VEHICLE_DATA_PATH, f"{vin}_complete.json")
    with open(complete_file, "w") as f:
        json.dump(complete_data, f, indent=4)
    
    return complete_data


def extract_key_vehicle_info(vehicle_info: Dict) -> Dict:
    """
    Extract key vehicle information from NHTSA response.
    
    Args:
        vehicle_info: Full vehicle info dictionary from NHTSA
        
    Returns:
        Dictionary with key fields only
    """
    key_fields = [
        "Model Year",
        "Make",
        "Model",
        "Trim",
        "Body Class",
        "Engine Number of Cylinders",
        "Fuel Type - Primary",
        "Displacement (L)",
        "Drive Type",
        "Transmission Style",
        "Vehicle Type",
        "Plant City",
        "Plant Country",
        "Manufacturer Name"
    ]
    
    extracted = {}
    for field in key_fields:
        if field in vehicle_info:
            extracted[field] = vehicle_info[field]
    
    return extracted


# Example usage for testing
if __name__ == "__main__":
    test_vin = "1HGCM82633A004352"
    
    print(f"Fetching complete vehicle data for VIN: {test_vin}")
    print("=" * 60)
    
    # Test complete data fetch
    complete_data = fetch_complete_vehicle_data(test_vin)
    
    print("\nVehicle Information:")
    key_info = extract_key_vehicle_info(complete_data["vehicle_info"])
    print(json.dumps(key_info, indent=2))
    
    print(f"\n\nRecalls Found: {complete_data['recall_count']}")
    if complete_data["recalls"]:
        print("\nRecall Details:")
        for i, recall in enumerate(complete_data["recalls"], 1):
            print(f"\n{i}. Campaign: {recall.get('NHTSACampaignNumber', 'N/A')}")
            print(f"   Component: {recall.get('Component', 'N/A')}")
            print(f"   Summary: {recall.get('Summary', 'N/A')[:100]}...")
    else:
        print("No recalls found for this vehicle.")

