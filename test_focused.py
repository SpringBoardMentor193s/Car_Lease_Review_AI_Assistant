"""Quick focused test for SLA extraction and negotiation"""
import requests
import json

BASE_URL = "http://localhost:8080"
CONTRACT_ID = "f5d511dc-4083-4892-ad51-b6e89a3b2ff1"
VIN = "1HGCM82633A004352"

print("="*80)
print("FOCUSED TEST: SLA Extraction & Negotiation")
print("="*80)

# Test 1: SLA Extraction
print("\n1. Testing SLA Extraction...")
print(f"Contract ID: {CONTRACT_ID}")

response = requests.post(f"{BASE_URL}/contract/{CONTRACT_ID}/extract-sla")

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("✓ SLA Extraction SUCCESS")
    print(f"\nFilename: {data.get('filename')}")
    print(f"VIN: {data.get('vin')}")
    print(f"SLA Extracted: {data.get('sla_extracted')}")
    print(f"\n{'='*80}")
    print("SLA DATA:")
    print(f"{'='*80}")
    print(data.get('sla_data', 'No data'))
    print(f"{'='*80}\n")
else:
    print(f"✗ SLA Extraction FAILED: {response.text}")

# Test 2: Negotiation Chatbot
print("\n2. Testing Negotiation Chatbot...")
print(f"VIN: {VIN}")

response = requests.post(
    f"{BASE_URL}/negotiate/{VIN}",
    data={"user_query": "I want to reduce my monthly payment. What should I negotiate?"}
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    if data.get('status') == 'success':
        print("✓ Negotiation Chatbot SUCCESS")
        print(f"\nVehicle: {data.get('vehicle')}")
        print(f"Has Recalls: {data.get('has_recalls')}")
        print(f"Recall Count: {data.get('recall_count')}")
        print(f"\n{'='*80}")
        print("NEGOTIATION ADVICE:")
        print(f"{'='*80}")
        print(data.get('negotiation_advice', 'No advice'))
        print(f"{'='*80}\n")
    else:
        print(f"✗ Negotiation returned error status")
        print(f"Error: {data.get('error', 'Unknown error')}")
else:
    print(f"✗ Negotiation FAILED: {response.text}")

print("\n" + "="*80)
print("TESTS COMPLETE")
print("="*80)
