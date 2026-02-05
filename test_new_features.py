"""
Test script for new authentication, conversation, and comparison features
Run this to validate all endpoints are working correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_section(message):
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}{Colors.END}\n")

# Global variables
auth_token = None
username = "testuser_" + datetime.now().strftime("%H%M%S")
conversation_id = None

def test_1_register():
    """Test user registration"""
    print_section("TEST 1: User Registration")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "testpassword123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"User registered: {data['user']['username']}")
            print_info(f"Email: {data['user']['email']}")
            return True
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_2_login():
    """Test user login and token generation"""
    print_section("TEST 2: User Login")
    
    global auth_token
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": username,
                "password": "testpassword123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data['access_token']
            print_success(f"Login successful for user: {data['username']}")
            print_info(f"Token: {auth_token[:50]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_3_get_user_info():
    """Test getting current user information"""
    print_section("TEST 3: Get Current User Info")
    
    if not auth_token:
        print_error("No auth token available. Skipping test.")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"User info retrieved: {data['username']}")
            print_info(f"Email: {data['email']}")
            print_info(f"Contract count: {data['contract_count']}")
            return True
        else:
            print_error(f"Failed to get user info: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_4_create_conversation():
    """Test creating a new conversation"""
    print_section("TEST 4: Create Conversation")
    
    global conversation_id
    
    if not auth_token:
        print_error("No auth token available. Skipping test.")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/conversations/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={
                "vin": "1HGCM82633A004352",
                "title": "Test Negotiation - Honda Accord"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            conversation_id = data['conversation_id']
            print_success(f"Conversation created: {conversation_id}")
            print_info(f"VIN: {data['vin']}")
            print_info(f"Title: {data['title']}")
            return True
        else:
            print_error(f"Failed to create conversation: {response.status_code}")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_5_list_conversations():
    """Test listing user conversations"""
    print_section("TEST 5: List Conversations")
    
    if not auth_token:
        print_error("No auth token available. Skipping test.")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {len(data['conversations'])} conversation(s)")
            for conv in data['conversations']:
                print_info(f"  - {conv['title']} ({conv['message_count']} messages)")
            return True
        else:
            print_error(f"Failed to list conversations: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_6_send_message():
    """Test sending a message in conversation"""
    print_section("TEST 6: Send Chat Message")
    
    if not auth_token or not conversation_id:
        print_error("No auth token or conversation ID. Skipping test.")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "conversation_id": conversation_id,
                "message": "What would be a fair monthly payment for this Honda Accord?"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Message sent successfully")
            print_info(f"AI Response (first 200 chars):\n{data['response'][:200]}...")
            return True
        else:
            print_error(f"Failed to send message: {response.status_code}")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_7_get_conversation():
    """Test retrieving conversation with messages"""
    print_section("TEST 7: Get Conversation Details")
    
    if not auth_token or not conversation_id:
        print_error("No auth token or conversation ID. Skipping test.")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Conversation retrieved: {data['title']}")
            print_info(f"Message count: {len(data['messages'])}")
            
            for i, msg in enumerate(data['messages'], 1):
                role_color = Colors.BLUE if msg['role'] == 'user' else Colors.GREEN
                print(f"{role_color}  Message {i} ({msg['role']}): {msg['content'][:100]}...{Colors.END}")
            
            return True
        else:
            print_error(f"Failed to get conversation: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_8_vehicle_data():
    """Test getting vehicle data"""
    print_section("TEST 8: Get Vehicle Data")
    
    try:
        response = requests.get(f"{BASE_URL}/vehicle/1HGCM82633A004352")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Vehicle data retrieved for VIN: {data['vin']}")
            
            vehicle = data.get('vehicle_info', {})
            print_info(f"  Make: {vehicle.get('Make')}")
            print_info(f"  Model: {vehicle.get('Model')}")
            print_info(f"  Year: {vehicle.get('ModelYear')}")
            print_info(f"  Recalls: {len(data.get('recalls', []))}")
            print_info(f"  Documents: {data.get('document_count', 0)}")
            
            return True
        else:
            print_error(f"Failed to get vehicle data: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_9_contract_summary():
    """Test getting contract summary (if contracts exist)"""
    print_section("TEST 9: Get Contract Summary")
    
    # Try to get a contract from vehicle data
    try:
        response = requests.get(f"{BASE_URL}/vehicle/1HGCM82633A004352")
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            
            if documents:
                contract_id = documents[0].get('contract_id')
                
                summary_response = requests.get(f"{BASE_URL}/contracts/{contract_id}/summary")
                
                if summary_response.status_code == 200:
                    summary = summary_response.json()
                    print_success(f"Contract summary retrieved: {contract_id}")
                    print_info(f"  Monthly Payment: ₹{summary.get('monthly_payment', 'N/A')}")
                    print_info(f"  Down Payment: ₹{summary.get('down_payment', 'N/A')}")
                    print_info(f"  Total Cost: ₹{summary.get('total_cost', 'N/A')}")
                    print_info(f"  Fairness Score: {summary.get('fairness_score', 'N/A')}/100")
                    return True
                else:
                    print_error(f"Failed to get contract summary: {summary_response.status_code}")
                    return False
            else:
                print_info("No contracts found for this VIN. Skipping test.")
                return True  # Not a failure
        else:
            print_error(f"Failed to get vehicle data: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_10_bad_login():
    """Test login with wrong credentials (should fail)"""
    print_section("TEST 10: Bad Login (Security Test)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": username,
                "password": "wrongpassword"
            }
        )
        
        if response.status_code == 401:
            print_success("Correctly rejected bad credentials (401)")
            return True
        else:
            print_error(f"Security issue: Bad login returned {response.status_code} instead of 401")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_11_unauthorized_access():
    """Test accessing protected endpoint without token"""
    print_section("TEST 11: Unauthorized Access (Security Test)")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        
        if response.status_code in [401, 403]:
            print_success(f"Correctly rejected unauthorized access ({response.status_code})")
            return True
        else:
            print_error(f"Security issue: Unauth access returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  CAR LEASE AI ASSISTANT - NEW FEATURES TEST SUITE")
    print(f"  Testing: Authentication, Conversations, Comparisons")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.END}\n")
    
    tests = [
        ("User Registration", test_1_register),
        ("User Login", test_2_login),
        ("Get User Info", test_3_get_user_info),
        ("Create Conversation", test_4_create_conversation),
        ("List Conversations", test_5_list_conversations),
        ("Send Chat Message", test_6_send_message),
        ("Get Conversation Details", test_7_get_conversation),
        ("Get Vehicle Data", test_8_vehicle_data),
        ("Get Contract Summary", test_9_contract_summary),
        ("Bad Login (Security)", test_10_bad_login),
        ("Unauthorized Access (Security)", test_11_unauthorized_access),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {status}  {test_name}")
    
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  Results: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if percentage == 100:
        print(f"  {Colors.GREEN}🎉 ALL TESTS PASSED! 🎉{Colors.END}")
    elif percentage >= 70:
        print(f"  {Colors.YELLOW}⚠️  Most tests passed, but some issues remain{Colors.END}")
    else:
        print(f"  {Colors.RED}❌ Many tests failed - check configuration{Colors.END}")
    
    print(f"{'='*60}{Colors.END}\n")
    
    # Print next steps
    if passed > 0:
        print_info("✨ Next steps:")
        print_info("  1. Open http://localhost:8080/demo to test the web UI")
        print_info("  2. Check FRONTEND_INTEGRATION_GUIDE.md for API documentation")
        print_info("  3. Start building your frontend/mobile app!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
    except Exception as e:
        print_error(f"Fatal error: {str(e)}")
