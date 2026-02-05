# Frontend Integration Guide

## 🎯 Overview
Complete API reference for frontend/mobile app integration with authentication, conversation threading, and contract comparison features.

## 🚀 Quick Start

### Base URL
```
http://localhost:8080
```

### Web Demo UI
Open in browser: **http://localhost:8080/demo**

---

## 🔐 Authentication Endpoints

### 1. Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "username": "john_doe",
    "email": "john@example.com",
    "contracts": []
  }
}
```

### 2. Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "john_doe"
}
```

**Store the token** in localStorage/AsyncStorage and include in all subsequent requests:
```javascript
localStorage.setItem('authToken', response.access_token);
```

### 3. Get Current User Info
```http
GET /auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "contract_count": 3,
  "contracts": [
    {
      "vin": "1HGCM82633A004352",
      "contract_id": "f5d511dc-4083-4892-ad51-b6e89a3b2ff1"
    }
  ]
}
```

---

## 📄 Contract Management

### 1. Upload Contract
```http
POST /upload
Content-Type: multipart/form-data

vin: 1HGCM82633A004352
file: <contract.pdf>
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('vin', '1HGCM82633A004352');
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8080/upload', {
  method: 'POST',
  body: formData
});
```

**Response:**
```json
{
  "contract_id": "f5d511dc-4083-4892-ad51-b6e89a3b2ff1",
  "vin": "1HGCM82633A004352",
  "text_extracted": "VEHICLE LEASE AGREEMENT...",
  "word_count": 1245
}
```

### 2. Extract SLA Parameters
```http
POST /contract/{contract_id}/extract-sla
```

**Response:**
```json
{
  "status": "success",
  "sla_data": {
    "monthly_payment": 15000,
    "down_payment": 100000,
    "lease_term_months": 36,
    "total_lease_amount": 640000,
    "interest_rate": 8.5,
    "security_deposit": 50000,
    "mileage_limit_km": 15000,
    "excess_mileage_charge_per_km": 10,
    "early_termination_penalty": 50000,
    "maintenance_included": true,
    "insurance_included": false,
    "fairness_score": 65
  },
  "recommendations": [
    "Monthly payment is competitive for this vehicle class",
    "Consider negotiating the down payment"
  ]
}
```

---

## 💬 Conversation Threading (Multi-Turn Chat)

### 1. Create New Conversation
```http
POST /conversations/create
Content-Type: multipart/form-data
Authorization: Bearer <token>

vin: 1HGCM82633A004352
title: Negotiation for Honda Accord
```

**Response:**
```json
{
  "conversation_id": "conv_abc123xyz",
  "vin": "1HGCM82633A004352",
  "title": "Negotiation for Honda Accord"
}
```

### 2. List All Conversations
```http
GET /conversations
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "conv_abc123xyz",
      "vin": "1HGCM82633A004352",
      "title": "Negotiation for Honda Accord",
      "message_count": 8,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:45:00Z"
    }
  ]
}
```

### 3. Get Conversation Details
```http
GET /conversations/{conversation_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conversation_id": "conv_abc123xyz",
  "user_id": "john_doe",
  "vin": "1HGCM82633A004352",
  "title": "Negotiation for Honda Accord",
  "messages": [
    {
      "role": "user",
      "content": "What's a fair monthly payment?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Based on the 2006 Honda Accord data...",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:45:00Z"
}
```

### 4. Send Message in Conversation
```http
POST /chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "conversation_id": "conv_abc123xyz",
  "message": "What should I offer as down payment?"
}
```

**Response:**
```json
{
  "conversation_id": "conv_abc123xyz",
  "response": "Based on our previous discussion about the Honda Accord, I recommend...",
  "vin": "1HGCM82633A004352"
}
```

---

## ⚖️ Contract Comparison

### 1. Compare Multiple Contracts
```http
POST /contracts/compare
Content-Type: application/json
Authorization: Bearer <token>

{
  "contract_ids": [
    "f5d511dc-4083-4892-ad51-b6e89a3b2ff1",
    "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "xyz789-1234-5678-abcd-efghij123456"
  ]
}
```

**Response:**
```json
{
  "comparison": {
    "contract_1": {
      "contract_id": "f5d511dc...",
      "monthly_payment": 15000,
      "down_payment": 100000,
      "lease_term": 36,
      "total_cost": 640000,
      "fairness_score": 65
    },
    "contract_2": {
      "contract_id": "a1b2c3d4...",
      "monthly_payment": 14500,
      "down_payment": 120000,
      "lease_term": 36,
      "total_cost": 642000,
      "fairness_score": 72
    },
    "contract_3": {
      "contract_id": "xyz789...",
      "monthly_payment": 15500,
      "down_payment": 80000,
      "lease_term": 36,
      "total_cost": 638000,
      "fairness_score": 58
    }
  },
  "winner": {
    "best_monthly_payment": "contract_2",
    "best_down_payment": "contract_3",
    "best_total_cost": "contract_3",
    "best_fairness": "contract_2"
  },
  "recommendation": "Contract 3 has the lowest total cost but lower fairness score..."
}
```

### 2. Get Contract Summary
```http
GET /contracts/{contract_id}/summary
```

**Response:**
```json
{
  "contract_id": "f5d511dc-4083-4892-ad51-b6e89a3b2ff1",
  "vin": "1HGCM82633A004352",
  "monthly_payment": 15000,
  "down_payment": 100000,
  "total_cost": 640000,
  "fairness_score": 65
}
```

---

## 🚗 Vehicle Data

### 1. Get Vehicle Info by VIN
```http
GET /vehicle/{vin}
```

**Response:**
```json
{
  "vin": "1HGCM82633A004352",
  "vehicle_info": {
    "Make": "HONDA",
    "Model": "Accord",
    "ModelYear": 2006,
    "engineCylinders": 6,
    "fuelTypePrimary": "Gasoline"
  },
  "recalls": [
    {
      "Component": "AIR BAGS",
      "Summary": "Takata airbag recall..."
    }
  ],
  "documents": [
    {
      "contract_id": "f5d511dc...",
      "filename": "contract.pdf"
    }
  ],
  "document_count": 1
}
```

---

## 🧠 AI Negotiation

### Legacy Endpoint (Single Turn)
```http
POST /negotiate/{vin}
Content-Type: application/json

{
  "query": "What's a fair price for this lease?"
}
```

**Use `/chat` endpoint instead for multi-turn conversations!**

---

## 📱 Frontend Implementation Examples

### React/JavaScript

#### Authentication Flow
```javascript
// Register
async function register(username, email, password) {
  const response = await fetch('http://localhost:8080/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  return await response.json();
}

// Login
async function login(username, password) {
  const response = await fetch('http://localhost:8080/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (response.ok) {
    localStorage.setItem('authToken', data.access_token);
    localStorage.setItem('username', data.username);
  }
  return data;
}

// Authenticated Request Helper
async function apiCall(url, options = {}) {
  const token = localStorage.getItem('authToken');
  const headers = {
    ...options.headers,
    'Authorization': token ? `Bearer ${token}` : undefined
  };
  
  return fetch(url, { ...options, headers });
}
```

#### Chat Interface
```javascript
// Create conversation
async function createConversation(vin, title) {
  const formData = new FormData();
  formData.append('vin', vin);
  formData.append('title', title);
  
  const response = await apiCall('http://localhost:8080/conversations/create', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// Send message
async function sendMessage(conversationId, message) {
  const response = await apiCall('http://localhost:8080/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, message })
  });
  
  return await response.json();
}

// Load conversation history
async function loadConversation(conversationId) {
  const response = await apiCall(`http://localhost:8080/conversations/${conversationId}`);
  return await response.json();
}
```

### Flutter/Dart

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8080';
  
  // Login
  static Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('authToken', data['access_token']);
      await prefs.setString('username', data['username']);
      return data;
    }
    throw Exception('Login failed');
  }
  
  // Chat
  static Future<Map<String, dynamic>> sendMessage(
    String conversationId,
    String message,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('authToken');
    
    final response = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'conversation_id': conversationId,
        'message': message,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to send message');
  }
}
```

---

## 🎨 UI/UX Recommendations

### Authentication Screen
- Login/Register tabs
- Remember me checkbox (store token securely)
- Password visibility toggle
- Forgot password link (future feature)

### Dashboard
- List of user's uploaded contracts
- Quick stats (contract count, average fairness score)
- Recent conversations
- Upload new contract button

### Contract Detail View
- Vehicle information card
- SLA parameters table
- Fairness score gauge (0-100)
- "Start Negotiation" button → Opens chat
- "Compare with others" button

### Chat Interface
- Message bubbles (user vs. assistant)
- Typing indicator while AI responds
- Conversation history dropdown
- New conversation button
- Clear/intuitive send button

### Comparison View
- Side-by-side contract cards
- Highlight best values in green
- Show differences clearly
- Overall recommendation banner

---

## 🔒 Security Best Practices

### Client-Side
1. **Store tokens securely**: Use httpOnly cookies or secure storage (KeyChain on iOS, KeyStore on Android)
2. **Never log tokens**: Avoid console.log or debug prints with sensitive data
3. **Check token expiration**: Tokens expire in 30 minutes. Implement refresh logic
4. **Logout on 401**: If you receive 401 Unauthorized, clear tokens and redirect to login

### Request Headers
```javascript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

### Error Handling
```javascript
async function handleApiResponse(response) {
  if (response.status === 401) {
    // Token expired or invalid
    localStorage.removeItem('authToken');
    window.location.href = '/login';
  } else if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API request failed');
  }
  return await response.json();
}
```

---

## 📊 Testing the API

### Using cURL

```bash
# Register
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}' \
  | jq -r '.access_token')

# Create conversation
curl -X POST http://localhost:8080/conversations/create \
  -H "Authorization: Bearer $TOKEN" \
  -F "vin=1HGCM82633A004352" \
  -F "title=Test Conversation"

# Send message
curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"conv_123","message":"What is a fair price?"}'
```

### Using Postman

1. **Set Base URL**: http://localhost:8080
2. **Create Environment Variable**: `authToken`
3. **Login Request**: Save response `access_token` to environment
4. **Subsequent Requests**: Add header `Authorization: Bearer {{authToken}}`

---

## 🐛 Troubleshooting

### "Unauthorized" Errors
- Check if token is included in Authorization header
- Verify token hasn't expired (30 min lifetime)
- Ensure token format is `Bearer <token>`, not just `<token>`

### "Conversation not found"
- Verify conversation_id exists by calling GET /conversations
- Ensure you're using the correct user's token
- Check if conversation belongs to logged-in user

### CORS Errors (Browser)
- Server already has CORS enabled for all origins
- If still seeing errors, check browser console for specific origin
- Ensure frontend URL matches (http vs https)

### Empty Responses
- Check if backend services are initialized
- Verify .env.local has GROQ_API_KEY
- Check backend/vehicle_data/ directory has VIN data

---

## 🚀 Next Steps

### For Web Frontend
1. Build React/Vue/Angular app using the API endpoints above
2. Implement authentication flow with token management
3. Create chat UI with message threading
4. Add contract upload and comparison views
5. Deploy frontend to Vercel/Netlify

### For Mobile App (Flutter)
1. Set up Flutter project with http package
2. Create API service class (see example above)
3. Build authentication screens
4. Implement chat screen with ListView.builder
5. Add contract management screens
6. Deploy to App Store/Play Store

---

## 📞 Support

- **API Documentation**: http://localhost:8080/docs
- **Demo UI**: http://localhost:8080/demo
- **GitHub Repository**: (Add your repo URL)
- **Issues**: (Add issues URL)

---

**Created**: January 2024  
**Version**: 2.0  
**Maintainer**: Car Lease Review AI Team
