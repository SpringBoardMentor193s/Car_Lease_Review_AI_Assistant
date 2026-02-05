"""
Test script for AI Negotiation Chatbot
Demonstrates how to use the negotiation API with existing vehicle data
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
VIN = "1HGCM82633A004352"  # Honda City VX from test data

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def test_negotiate_basic():
    """Test basic negotiation without specific query"""
    print_section("TEST 1: Basic Price Negotiation")
    
    response = requests.post(
        f"{BASE_URL}/negotiate/{VIN}",
        data={"user_query": ""}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Vehicle: {result['vehicle']['year']} {result['vehicle']['make']} {result['vehicle']['model']}")
        print(f"Has Recalls: {result['has_recalls']} ({result['recall_count']} recalls)")
        print(f"\nNEGOTIATION ADVICE:\n")
        print(result['negotiation_advice'])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_negotiate_specific_query():
    """Test negotiation with specific user query"""
    print_section("TEST 2: Specific Negotiation Query")
    
    query = "I want to reduce my monthly payment from ₹22,000 to ₹18,000. How can I negotiate this?"
    
    response = requests.post(
        f"{BASE_URL}/negotiate/{VIN}",
        data={"user_query": query}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"User Query: {query}\n")
        print(f"Vehicle: {result['vehicle']['year']} {result['vehicle']['make']} {result['vehicle']['model']}")
        print(f"\nNEGOTIATION ADVICE:\n")
        print(result['negotiation_advice'])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_negotiate_down_payment():
    """Test negotiation focused on down payment"""
    print_section("TEST 3: Down Payment Negotiation")
    
    query = "The down payment of ₹1,50,000 is too high. What should I offer instead?"
    
    response = requests.post(
        f"{BASE_URL}/negotiate/{VIN}",
        data={"user_query": query}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"User Query: {query}\n")
        print(result['negotiation_advice'])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_extract_sla():
    """Test SLA extraction from contract"""
    print_section("TEST 4: SLA Extraction with Fairness Score")
    
    # First, get the contract ID
    response = requests.get(f"{BASE_URL}/vehicle/{VIN}/complete")
    if response.status_code == 200:
        data = response.json()
        documents = data.get('documents', [])
        if documents:
            contract_id = documents[0]['document_id']
            print(f"Contract ID: {contract_id}")
            
            # Extract SLA
            sla_response = requests.post(
                f"{BASE_URL}/contract/{contract_id}/extract-sla"
            )
            
            if sla_response.status_code == 200:
                sla_result = sla_response.json()
                print(f"\nContract: {sla_result['filename']}")
                print(f"VIN: {sla_result['vin']}")
                print(f"SLA Extracted: {sla_result['sla_extracted']}")
                print(f"\nSLA DATA:\n")
                print(sla_result['sla_data'])
            else:
                print(f"SLA Extraction Error: {sla_response.status_code}")
                print(sla_response.text)
        else:
            print("No documents found for this VIN")
    else:
        print(f"Error fetching vehicle data: {response.status_code}")

def test_get_vehicle_complete():
    """Test getting complete vehicle data"""
    print_section("TEST 5: Complete Vehicle Data")
    
    response = requests.get(f"{BASE_URL}/vehicle/{VIN}/complete")
    
    if response.status_code == 200:
        data = response.json()
        print(f"VIN: {data['vin']}")
        print(f"Document Count: {data['document_count']}")
        print(f"Recalls: {len(data.get('recalls', []))}")
        print(f"\nVehicle Info:")
        vehicle_info = data.get('vehicle_info', {})
        for key, value in vehicle_info.items():
            print(f"  {key}: {value}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  AI NEGOTIATION CHATBOT - TEST SUITE")
    print("  Make sure the server is running on http://localhost:8080")
    print("  Make sure GROQ_API_KEY is set in .env.local")
    print("="*70)
    
    try:
        # Test if server is running
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("\n❌ Server is not running or not responding")
            print("Start the server with: cd backend && uvicorn main:app --reload --port 8080")
            return
        
        print("\n✅ Server is running")
        
        # Run tests
        test_get_vehicle_complete()
        
        # Negotiation tests (require GROQ_API_KEY)
        print("\n⚠️  The following tests require GROQ_API_KEY to be set in .env.local")
        choice = input("\nProceed with AI tests? (y/n): ")
        
        if choice.lower() == 'y':
            test_negotiate_basic()
            test_negotiate_specific_query()
            test_negotiate_down_payment()
            test_extract_sla()
        else:
            print("\n✅ Skipped AI tests. Set GROQ_API_KEY and run again.")
        
        print("\n" + "="*70)
        print("  TESTS COMPLETED")
        print("="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server at http://localhost:8080")
        print("Start the server with: cd backend && uvicorn main:app --reload --port 8080")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
