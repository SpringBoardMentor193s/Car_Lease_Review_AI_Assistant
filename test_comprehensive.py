"""
Comprehensive Test Suite for Car Lease Review AI Assistant
Tests: OCR Quality, SLA Extraction, Negotiation Chatbot, End-to-End Workflows
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8080"
TEST_VIN = "1HGCM82633A004352"

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title):
    """Print formatted test section header"""
    print("\n" + "="*80)
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print("="*80)

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name):
        self.passed += 1
        self.tests.append((test_name, "PASS"))
        print_success(test_name)
    
    def add_fail(self, test_name, error=""):
        self.failed += 1
        self.tests.append((test_name, f"FAIL: {error}"))
        print_error(f"{test_name} - {error}")
    
    def add_warning(self, test_name, warning=""):
        self.warnings += 1
        self.tests.append((test_name, f"WARN: {warning}"))
        print_warning(f"{test_name} - {warning}")
    
    def summary(self):
        print_header("TEST SUMMARY")
        total = self.passed + self.failed + self.warnings
        print(f"\n{Colors.BOLD}Total Tests: {total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Passed: {self.passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.failed}{Colors.ENDC}")
        print(f"{Colors.WARNING}Warnings: {self.warnings}{Colors.ENDC}")
        
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.ENDC}")
        
        if self.failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}")


results = TestResults()


def test_server_connectivity():
    """Test 1: Verify server is running"""
    print_header("TEST 1: Server Connectivity")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.add_pass("Server is running and responsive")
            print_info(f"Server: {data.get('message', 'Unknown')}")
            print_info(f"Storage: {data.get('storage', 'Unknown')}")
            return True
        else:
            results.add_fail("Server connectivity", f"Status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        results.add_fail("Server connectivity", "Cannot connect to http://localhost:8080")
        print_error("Start server with: cd backend && uvicorn main:app --reload --port 8080")
        return False
    except Exception as e:
        results.add_fail("Server connectivity", str(e))
        return False


def test_ocr_quality():
    """Test 2: Validate OCR Quality"""
    print_header("TEST 2: OCR Quality Validation")
    
    try:
        # Get complete vehicle data
        response = requests.get(f"{BASE_URL}/vehicle/{TEST_VIN}/complete")
        
        if response.status_code != 200:
            results.add_fail("OCR quality check", "Cannot fetch vehicle data")
            return
        
        data = response.json()
        documents = data.get('documents', [])
        
        if not documents:
            results.add_warning("OCR quality check", "No documents found for testing")
            return
        
        print_info(f"Analyzing {len(documents)} document(s)")
        
        ocr_passed = 0
        ocr_failed = 0
        
        for i, doc in enumerate(documents, 1):
            ocr_text = doc.get('ocr_text', '')
            filename = doc.get('filename', 'Unknown')
            
            print(f"\n{Colors.BOLD}Document {i}: {filename}{Colors.ENDC}")
            
            # Check if OCR was successful
            if "Tesseract OCR not installed" in ocr_text:
                results.add_fail(f"OCR - Document {i}", "Tesseract not installed")
                ocr_failed += 1
                continue
            
            # Validate OCR quality metrics
            if len(ocr_text) < 50:
                results.add_warning(f"OCR - Document {i}", f"Very short text ({len(ocr_text)} chars)")
                print_warning(f"  Text length: {len(ocr_text)} characters (might be low quality)")
            else:
                print_info(f"  Text length: {len(ocr_text)} characters")
            
            # Check for key lease/loan terms
            key_terms = ['lease', 'payment', 'monthly', 'vin', 'vehicle', 'contract', 
                        'lessor', 'lessee', 'term', 'agreement', 'price', 'down payment']
            found_terms = [term for term in key_terms if term.lower() in ocr_text.lower()]
            
            print_info(f"  Key terms found: {len(found_terms)}/{len(key_terms)}")
            
            if len(found_terms) >= 3:
                results.add_pass(f"OCR quality - Document {i} ({filename})")
                ocr_passed += 1
                print_info(f"  Terms: {', '.join(found_terms[:5])}")
            else:
                results.add_warning(f"OCR quality - Document {i}", 
                                  f"Only {len(found_terms)} key terms found")
            
            # Show sample text
            sample = ocr_text[:200].replace('\n', ' ')
            print_info(f"  Sample: {sample}...")
        
        print(f"\n{Colors.BOLD}OCR Summary:{Colors.ENDC}")
        print(f"  Good quality: {ocr_passed}")
        print(f"  Failed/Low quality: {ocr_failed}")
        
    except Exception as e:
        results.add_fail("OCR quality check", str(e))


def test_sla_extraction():
    """Test 3: SLA Extraction Accuracy"""
    print_header("TEST 3: SLA Extraction Accuracy")
    
    try:
        # Get available contracts
        response = requests.get(f"{BASE_URL}/vehicle/{TEST_VIN}/complete")
        
        if response.status_code != 200:
            results.add_fail("SLA extraction", "Cannot fetch vehicle data")
            return
        
        data = response.json()
        documents = data.get('documents', [])
        
        if not documents:
            results.add_warning("SLA extraction", "No documents available for extraction")
            return
        
        # Test on first valid document
        test_doc = None
        for doc in documents:
            if "Tesseract OCR not installed" not in doc.get('ocr_text', ''):
                test_doc = doc
                break
        
        if not test_doc:
            results.add_fail("SLA extraction", "No valid OCR text available")
            return
        
        contract_id = test_doc.get('document_id')
        filename = test_doc.get('filename', 'Unknown')
        
        print_info(f"Testing extraction on: {filename}")
        print_info(f"Contract ID: {contract_id}")
        
        # Extract SLA
        print(f"\n{Colors.BOLD}Calling AI to extract SLA parameters...{Colors.ENDC}")
        start_time = time.time()
        
        sla_response = requests.post(f"{BASE_URL}/contract/{contract_id}/extract-sla")
        
        extraction_time = time.time() - start_time
        
        if sla_response.status_code != 200:
            results.add_fail("SLA extraction API", f"Status: {sla_response.status_code}")
            print_error(f"Error: {sla_response.text}")
            return
        
        sla_data = sla_response.json()
        
        print_info(f"Extraction completed in {extraction_time:.2f} seconds")
        
        # Validate extraction
        if sla_data.get('sla_extracted'):
            results.add_pass("SLA extraction successful")
        else:
            results.add_fail("SLA extraction", "Extraction flag not set")
        
        # Check SLA data content
        sla_content = sla_data.get('sla_data', '')
        
        if not sla_content:
            results.add_fail("SLA data content", "Empty response")
            return
        
        print(f"\n{Colors.BOLD}Extracted SLA Data:{Colors.ENDC}")
        print("-" * 80)
        print(sla_content)
        print("-" * 80)
        
        # Check for required parameters
        required_params = [
            'interest', 'apr', 'rate',
            'term', 'month',
            'payment',
            'down payment',
            'residual',
            'mileage',
            'fee'
        ]
        
        found_params = [param for param in required_params if param.lower() in sla_content.lower()]
        
        print(f"\n{Colors.BOLD}Parameter Coverage:{Colors.ENDC}")
        print_info(f"Found {len(found_params)}/{len(required_params)} parameter types")
        
        if len(found_params) >= 7:
            results.add_pass(f"SLA parameter coverage ({len(found_params)}/11 types)")
        else:
            results.add_warning("SLA parameter coverage", 
                              f"Only {len(found_params)} parameter types found")
        
        # Check for fairness score
        if 'fairness' in sla_content.lower() or 'score' in sla_content.lower():
            results.add_pass("Contract Fairness Score included")
        else:
            results.add_warning("Fairness score", "Score not clearly identified")
        
    except Exception as e:
        results.add_fail("SLA extraction", str(e))


def test_negotiation_chatbot():
    """Test 4: AI Negotiation Chatbot"""
    print_header("TEST 4: AI Negotiation Chatbot")
    
    try:
        query = "How can I negotiate a better deal on this lease?"
        
        print_info(f"Testing with query: '{query}'")
        print(f"\n{Colors.BOLD}Calling AI chatbot...{Colors.ENDC}")
        
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/negotiate/{TEST_VIN}",
            data={"user_query": query}
        )
        
        response_time = time.time() - start_time
        
        if response.status_code != 200:
            results.add_fail("Negotiation chatbot API", f"Status: {response.status_code}")
            print_error(f"Error: {response.text}")
            return
        
        result = response.json()
        
        print_info(f"Response received in {response_time:.2f} seconds")
        
        # Validate response structure
        if result.get('status') == 'success':
            results.add_pass("Negotiation API successful")
        else:
            results.add_fail("Negotiation API", f"Status: {result.get('status')}")
            return
        
        # Check vehicle info
        vehicle = result.get('vehicle', {})
        if vehicle.get('vin') == TEST_VIN:
            results.add_pass("Vehicle information correct")
        
        # Check negotiation advice
        advice = result.get('negotiation_advice', '')
        
        if not advice:
            results.add_fail("Negotiation advice", "Empty response")
            return
        
        print(f"\n{Colors.BOLD}Negotiation Advice:{Colors.ENDC}")
        print("-" * 80)
        print(advice[:1000])  # Show first 1000 chars
        if len(advice) > 1000:
            print(f"... (truncated, total {len(advice)} characters)")
        print("-" * 80)
        
        # Quality checks
        quality_indicators = [
            'payment', 'saving', 'negotiate', 'deal', 'price',
            'recommend', 'reduce', 'opportunity', 'term'
        ]
        
        found_indicators = [ind for ind in quality_indicators if ind.lower() in advice.lower()]
        
        print(f"\n{Colors.BOLD}Response Quality:{Colors.ENDC}")
        print_info(f"Length: {len(advice)} characters")
        print_info(f"Quality indicators: {len(found_indicators)}/{len(quality_indicators)}")
        
        if len(found_indicators) >= 5:
            results.add_pass(f"Negotiation advice quality ({len(found_indicators)} indicators)")
        else:
            results.add_warning("Advice quality", "Limited negotiation guidance")
        
        # Check for specific recommendations
        if any(word in advice.lower() for word in ['$', '₹', 'rupee', 'dollar', '%']):
            results.add_pass("Specific financial recommendations included")
        else:
            results.add_warning("Financial specifics", "No clear dollar/percentage amounts")
        
        # Check recall information
        if result.get('has_recalls'):
            print_info(f"Recalls found: {result.get('recall_count', 0)}")
            if 'recall' in advice.lower():
                results.add_pass("Recall information utilized in advice")
            else:
                results.add_warning("Recall leverage", "Recalls not mentioned in advice")
        
    except Exception as e:
        results.add_fail("Negotiation chatbot", str(e))


def test_end_to_end_workflow():
    """Test 5: End-to-End Workflow"""
    print_header("TEST 5: End-to-End Workflow Test")
    
    try:
        print(f"{Colors.BOLD}Simulating complete user workflow:{Colors.ENDC}")
        print("1. Get vehicle data")
        print("2. Review documents")
        print("3. Extract SLA")
        print("4. Get negotiation advice")
        
        # Step 1: Get complete vehicle data
        print(f"\n{Colors.BOLD}Step 1: Fetching complete vehicle data...{Colors.ENDC}")
        response = requests.get(f"{BASE_URL}/vehicle/{TEST_VIN}/complete")
        
        if response.status_code == 200:
            data = response.json()
            results.add_pass("Step 1: Vehicle data fetched")
            
            vehicle_info = data.get('vehicle_info', {})
            print_info(f"Vehicle: {vehicle_info.get('ModelYear')} {vehicle_info.get('Make')} {vehicle_info.get('Model')}")
            print_info(f"Documents: {data.get('document_count', 0)}")
            print_info(f"Recalls: {len(data.get('recalls', []))}")
        else:
            results.add_fail("Step 1", "Failed to fetch vehicle data")
            return
        
        # Step 2: Review documents
        print(f"\n{Colors.BOLD}Step 2: Reviewing document quality...{Colors.ENDC}")
        documents = data.get('documents', [])
        
        if documents:
            valid_docs = [d for d in documents if "Tesseract" not in d.get('ocr_text', '')]
            results.add_pass(f"Step 2: Found {len(valid_docs)} valid document(s)")
        else:
            results.add_warning("Step 2", "No documents available")
            return
        
        # Step 3: Extract SLA
        print(f"\n{Colors.BOLD}Step 3: Extracting SLA from first document...{Colors.ENDC}")
        
        if valid_docs:
            contract_id = valid_docs[0].get('document_id')
            sla_response = requests.post(f"{BASE_URL}/contract/{contract_id}/extract-sla")
            
            if sla_response.status_code == 200:
                results.add_pass("Step 3: SLA extraction successful")
                sla_result = sla_response.json()
                
                # Extract fairness score if present
                sla_text = str(sla_result.get('sla_data', ''))
                import re
                score_match = re.search(r'(\d+)\s*/\s*100', sla_text)
                if score_match:
                    score = score_match.group(1)
                    print_info(f"Contract Fairness Score: {score}/100")
            else:
                results.add_fail("Step 3", "SLA extraction failed")
        
        # Step 4: Get negotiation advice
        print(f"\n{Colors.BOLD}Step 4: Getting AI negotiation advice...{Colors.ENDC}")
        
        neg_response = requests.post(
            f"{BASE_URL}/negotiate/{TEST_VIN}",
            data={"user_query": "Based on the contract, what should I negotiate?"}
        )
        
        if neg_response.status_code == 200:
            results.add_pass("Step 4: Negotiation advice generated")
            neg_result = neg_response.json()
            
            advice = neg_result.get('negotiation_advice', '')
            # Extract potential savings if mentioned
            import re
            savings_matches = re.findall(r'[₹$]\s*[\d,]+', advice)
            if savings_matches:
                print_info(f"Potential savings identified: {len(savings_matches)} areas")
        else:
            results.add_fail("Step 4", "Negotiation advice failed")
        
        # Final workflow validation
        print(f"\n{Colors.BOLD}Workflow Validation:{Colors.ENDC}")
        results.add_pass("Complete end-to-end workflow executed successfully")
        
    except Exception as e:
        results.add_fail("End-to-end workflow", str(e))


def test_api_response_times():
    """Test 6: API Performance"""
    print_header("TEST 6: API Performance & Response Times")
    
    endpoints = [
        ("GET", f"/vehicle/{TEST_VIN}", "Vehicle lookup"),
        ("GET", f"/vehicle/{TEST_VIN}/recalls", "Recall check"),
        ("GET", f"/vehicle/{TEST_VIN}/complete", "Complete data"),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            start = time.time()
            
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                if elapsed < 2.0:
                    results.add_pass(f"{description} - {elapsed:.2f}s (fast)")
                elif elapsed < 5.0:
                    results.add_warning(f"{description} - {elapsed:.2f}s", "Slower than expected")
                else:
                    results.add_warning(f"{description} - {elapsed:.2f}s", "Very slow")
            else:
                results.add_fail(f"{description}", f"Status {response.status_code}")
                
        except Exception as e:
            results.add_fail(f"{description}", str(e))


def main():
    """Run all tests"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}CAR LEASE REVIEW AI ASSISTANT - COMPREHENSIVE TEST SUITE{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"\nTesting against: {BASE_URL}")
    print(f"Test VIN: {TEST_VIN}")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test 1: Server connectivity (prerequisite)
    if not test_server_connectivity():
        print_error("\n⚠️  Server is not running. Cannot proceed with tests.")
        print_info("Start server: cd backend && uvicorn main:app --reload --port 8080")
        return
    
    # Test 2: OCR Quality
    test_ocr_quality()
    
    # Test 3: SLA Extraction
    test_sla_extraction()
    
    # Test 4: Negotiation Chatbot
    test_negotiation_chatbot()
    
    # Test 5: End-to-End Workflow
    test_end_to_end_workflow()
    
    # Test 6: Performance
    test_api_response_times()
    
    # Print summary
    results.summary()
    
    # Recommendations
    print_header("RECOMMENDATIONS")
    
    if results.failed > 0:
        print(f"\n{Colors.FAIL}Issues to address:{Colors.ENDC}")
        for test_name, status in results.tests:
            if status.startswith("FAIL"):
                print(f"  • {test_name}: {status}")
    
    if results.warnings > 0:
        print(f"\n{Colors.WARNING}Areas for improvement:{Colors.ENDC}")
        for test_name, status in results.tests:
            if status.startswith("WARN"):
                print(f"  • {test_name}: {status}")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print("  1. Review any failed tests and fix issues")
    print("  2. Check OCR quality on uploaded contracts")
    print("  3. Verify SLA extraction includes all 11 parameters")
    print("  4. Test with different contract types")
    print("  5. Monitor AI response quality and accuracy")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
