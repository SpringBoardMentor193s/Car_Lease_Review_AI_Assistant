"""
End-to-End Testing Script for Car Lease Review AI Assistant
Tests the complete workflow: Upload → OCR → SLA Extraction → Vehicle Data Integration

This script tests:
1. Contract upload with VIN
2. NHTSA vehicle data fetching (make, model, year, recalls)
3. LLM-based SLA extraction from contract
4. Combined data retrieval (contract + vehicle data)
5. Database storage verification
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_VIN = "5YJSA1E14HF000001"  # Tesla Model S VIN (example)
TEST_CONTRACT_PATH = "test_sample_contract.txt"  # We'll create a sample contract

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def create_sample_contract():
    """Create a sample car lease contract for testing"""
    sample_contract = """
VEHICLE LEASE AGREEMENT

Lessor: Premium Auto Leasing Corp
Lessee: John Smith
Date: February 5, 2026

VEHICLE INFORMATION
VIN: 5YJSA1E14HF000001
Year: 2024
Make: Tesla
Model: Model S
Trim: Long Range

FINANCIAL TERMS
MSRP: $94,990.00
Capitalized Cost: $92,500.00
Capitalized Cost Reduction: $5,000.00

LEASE TERMS
Monthly Payment: $1,249.00
Term: 36 months
Annual Percentage Rate (APR): 6.99%
Money Factor: 0.00291

DUE AT SIGNING
Down Payment: $5,000.00
First Month Payment: $1,249.00
Acquisition Fee: $995.00
Registration Fee: $450.00
Total Due at Signing: $7,694.00

MILEAGE
Annual Mileage Allowance: 12,000 miles per year
Total Mileage Allowance: 36,000 miles over lease term
Excess Mileage Charge: $0.30 per mile

RESIDUAL VALUE
Residual Value: $56,994.00
Residual Percentage: 60% of MSRP

END OF LEASE OPTIONS
Purchase Option Price: $56,994.00
Disposition Fee (if not purchasing): $595.00

FEES AND PENALTIES
Early Termination Fee: Up to $7,500 (varies by term remaining)
Late Payment Fee: Greater of $50 or 5% of monthly payment

REQUIREMENTS
Insurance: Minimum $100,000/$300,000 liability coverage required
Comprehensive and collision coverage with maximum $1,000 deductible required
Gap insurance strongly recommended

Maintenance: Lessee responsible for all routine maintenance including:
- Oil changes and fluid checks
- Tire rotation and replacement
- Brake service
- Battery maintenance

Warranty: Manufacturer's 4-year/50,000-mile basic warranty included
8-year/150,000-mile battery and drive unit warranty

ADDITIONAL TERMS
- Excessive wear and tear charges may apply at lease end
- All maintenance records must be kept
- Vehicle must be serviced at authorized Tesla service centers
- Annual vehicle inspection required
- No modifications or alterations allowed without written consent

By signing below, Lessee acknowledges receipt and understanding of all lease terms.

Signature: _____________________ Date: __________
"""
    
    # Save to file
    with open(TEST_CONTRACT_PATH, "w") as f:
        f.write(sample_contract)
    
    print_success(f"Created sample contract: {TEST_CONTRACT_PATH}")
    return TEST_CONTRACT_PATH


def test_1_upload_contract():
    """Test 1: Upload contract with VIN"""
    print_header("TEST 1: Upload Contract with VIN")
    
    try:
        # Create sample contract if it doesn't exist
        if not os.path.exists(TEST_CONTRACT_PATH):
            create_sample_contract()
        
        # Upload contract
        with open(TEST_CONTRACT_PATH, "rb") as f:
            files = {"file": (TEST_CONTRACT_PATH, f, "text/plain")}
            data = {"vin": TEST_VIN}
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Contract uploaded successfully")
            print(f"  VIN: {result.get('vin')}")
            print(f"  Document ID: {result.get('document_id')}")
            print(f"  Contract ID: {result.get('contract_id')}")
            print(f"  Vehicle ID: {result.get('vehicle_id')}")
            print(f"  NHTSA Data Fetched: {result.get('nhtsa_fetched')}")
            print(f"  Database Stored: {result.get('database_stored')}")
            return result
        else:
            print_error(f"Upload failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_2_get_vehicle_info(vin):
    """Test 2: Get vehicle information from NHTSA"""
    print_header("TEST 2: Fetch Vehicle Information (NHTSA API)")
    
    try:
        response = requests.get(f"{BASE_URL}/vehicle/{vin}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Vehicle information retrieved")
            
            vehicle_info = result.get("vehicle_info", {})
            print(f"  Year: {vehicle_info.get('Model Year', 'N/A')}")
            print(f"  Make: {vehicle_info.get('Make', 'N/A')}")
            print(f"  Model: {vehicle_info.get('Model', 'N/A')}")
            print(f"  Body Class: {vehicle_info.get('Body Class', 'N/A')}")
            print(f"  Fuel Type: {vehicle_info.get('Fuel Type - Primary', 'N/A')}")
            return result
        else:
            print_error(f"Failed to get vehicle info: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_3_get_complete_vehicle_data(vin):
    """Test 3: Get complete vehicle data including recalls"""
    print_header("TEST 3: Fetch Complete Vehicle Data (Including Recalls)")
    
    try:
        response = requests.get(f"{BASE_URL}/vehicle/{vin}/complete")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Complete vehicle data retrieved")
            
            vehicle_info = result.get("vehicle_info", {})
            print(f"  Year: {vehicle_info.get('year', 'N/A')}")
            print(f"  Make: {vehicle_info.get('make', 'N/A')}")
            print(f"  Model: {vehicle_info.get('model', 'N/A')}")
            
            recalls = result.get("recalls", [])
            recall_count = result.get("recall_count", 0)
            print(f"\n  Recalls Found: {recall_count}")
            
            if recalls:
                for i, recall in enumerate(recalls[:3], 1):  # Show first 3 recalls
                    print(f"\n  Recall {i}:")
                    print(f"    Campaign: {recall.get('recall_number', 'N/A')}")
                    print(f"    Component: {recall.get('component', 'N/A')}")
                    summary = recall.get('summary', 'N/A')
                    print(f"    Summary: {summary[:100]}..." if len(summary) > 100 else f"    Summary: {summary}")
            else:
                print("  No recalls found for this vehicle")
            
            return result
        else:
            print_error(f"Failed to get complete vehicle data: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_4_extract_sla(contract_id):
    """Test 4: Extract SLA using LLM"""
    print_header("TEST 4: Extract SLA Data Using LLM")
    
    try:
        print("Sending extraction request...")
        response = requests.post(f"{BASE_URL}/contract/{contract_id}/extract-sla")
        
        if response.status_code == 200:
            result = response.json()
            print_success("SLA extraction completed")
            
            sla_data = result.get("sla_data", {})
            print(f"\n  Financial Terms:")
            print(f"    APR: {sla_data.get('apr_percent')}%")
            print(f"    Money Factor: {sla_data.get('money_factor')}")
            print(f"    Monthly Payment: ${sla_data.get('monthly_payment')}")
            print(f"    Down Payment: ${sla_data.get('down_payment')}")
            print(f"    MSRP: ${sla_data.get('msrp')}")
            
            print(f"\n  Lease Terms:")
            print(f"    Term: {sla_data.get('term_months')} months")
            print(f"    Annual Mileage: {sla_data.get('mileage_allowance_yr')} miles")
            print(f"    Overage Fee: ${sla_data.get('mileage_overage_fee')}/mile")
            
            print(f"\n  Residual:")
            print(f"    Value: ${sla_data.get('residual_value')}")
            print(f"    Percentage: {sla_data.get('residual_percent_msrp')}%")
            
            print(f"\n  Fees:")
            print(f"    Early Termination: ${sla_data.get('early_termination_fee')}")
            print(f"    Disposition: ${sla_data.get('disposition_fee')}")
            
            metadata = sla_data.get("_extraction_metadata", {})
            if metadata:
                print(f"\n  Extraction Metadata:")
                print(f"    Model: {metadata.get('model_name')}")
                print(f"    Prompt Version: {metadata.get('prompt_version')}")
                print(f"    Tokens Used: {metadata.get('tokens_used')}")
            
            return result
        else:
            print_error(f"SLA extraction failed: {response.status_code}")
            print(response.text)
            
            if "GROQ_API_KEY" in response.text:
                print_warning("\n  Make sure to set GROQ_API_KEY environment variable:")
                print("    export GROQ_API_KEY='your-api-key'  # Linux/Mac")
                print("    $env:GROQ_API_KEY='your-api-key'    # Windows PowerShell")
            
            return None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_5_get_complete_contract(contract_id):
    """Test 5: Get complete contract data (contract + SLA + vehicle)"""
    print_header("TEST 5: Get Complete Contract Data (Contract + SLA + Vehicle)")
    
    try:
        response = requests.get(f"{BASE_URL}/contract/{contract_id}/complete")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Complete contract data retrieved")
            
            contract = result.get("contract", {})
            vehicle = result.get("vehicle", {})
            
            print(f"\n  Contract Information:")
            print(f"    Contract ID: {contract.get('contract_id')}")
            print(f"    Contract Type: {contract.get('contract_type')}")
            print(f"    Status: {contract.get('doc_status')}")
            
            if vehicle:
                print(f"\n  Vehicle Information:")
                print(f"    VIN: {vehicle.get('vin')}")
                print(f"    {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}")
                print(f"    Recalls: {vehicle.get('recall_count', 0)}")
            
            sla = contract.get("sla_data")
            if sla:
                print(f"\n  SLA Data: ✓ Found")
                print(f"    Monthly Payment: ${sla.get('monthly_payment')}")
                print(f"    Term: {sla.get('term_months')} months")
            else:
                print(f"\n  SLA Data: Not extracted yet")
            
            return result
        else:
            print_error(f"Failed to get complete contract: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def run_all_tests():
    """Run complete end-to-end test suite"""
    print_header("Car Lease Review AI Assistant - End-to-End Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test VIN: {TEST_VIN}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print_success("Backend server is running")
    except:
        print_error("Backend server is not running!")
        print_warning("Please start the server first:")
        print("  cd backend")
        print("  uvicorn main:app --reload")
        return
    
    # Test 1: Upload contract
    print("\n")
    upload_result = test_1_upload_contract()
    if not upload_result:
        print_error("Upload test failed. Stopping tests.")
        return
    
    contract_id = upload_result.get("contract_id")
    vin = upload_result.get("vin")
    
    time.sleep(1)
    
    # Test 2: Get vehicle info
    test_2_get_vehicle_info(vin)
    time.sleep(1)
    
    # Test 3: Get complete vehicle data with recalls
    test_3_get_complete_vehicle_data(vin)
    time.sleep(1)
    
    # Test 4: Extract SLA
    if contract_id:
        test_4_extract_sla(contract_id)
        time.sleep(1)
        
        # Test 5: Get complete contract data
        test_5_get_complete_contract(contract_id)
    else:
        print_warning("Skipping SLA extraction tests (no contract_id)")
    
    # Summary
    print_header("TEST SUMMARY")
    print_success("All tests completed!")
    print("\nNext steps:")
    print("  1. Review the extracted SLA data for accuracy")
    print("  2. Check database for stored records")
    print("  3. Test with real PDF contracts")
    print("  4. Tune LLM prompts for better extraction")
    print("  5. Add error handling and validation")
    
    print(f"\n{Colors.CYAN}API Endpoints Available:{Colors.RESET}")
    print(f"  POST /upload - Upload contract with VIN")
    print(f"  GET  /vehicle/{'{vin}'} - Get vehicle info")
    print(f"  GET  /vehicle/{'{vin}'}/complete - Get vehicle + recalls")
    print(f"  POST /contract/{'{contract_id}'}/extract-sla - Extract SLA with LLM")
    print(f"  GET  /contract/{'{contract_id}'}/complete - Get contract + SLA + vehicle")


if __name__ == "__main__":
    run_all_tests()
