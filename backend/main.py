"""
Simple JSON-only version of the Car Lease Review API
No database required - all data stored as JSON files
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import os, uuid, json
from dotenv import load_dotenv
from services.ocr_service import extract_text
from services.nhtsa_service import fetch_vehicle_data, fetch_vehicle_recalls, fetch_complete_vehicle_data
from services.llm_service import get_llm_service
from services.auth_service import (
    authenticate_user, create_user, create_access_token, 
    decode_access_token, get_user, add_user_contract,
    get_user_contracts, ACCESS_TOKEN_EXPIRE_MINUTES
)
from services.conversation_service import (
    create_conversation, get_conversation, add_message,
    get_user_conversations, get_conversation_context
)
from services.comparison_service import compare_contracts, get_contract_summary
from datetime import timedelta

# Load environment variables from .env.local or .env
load_dotenv(dotenv_path="../.env.local")
load_dotenv(dotenv_path="../.env")

app = FastAPI(title="Car Lease Review API (JSON Storage)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "vehicle_data"
UPLOAD_DIR = "uploads/contracts"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Security
security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class CompareRequest(BaseModel):
    contract_ids: List[str]


# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    token = credentials.credentials
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Car Lease Review AI Assistant API",
        "storage": "JSON-only (no database)",
        "features": ["OCR", "SLA Extraction", "AI Negotiation", "VIN Lookup", "User Auth", "Conversations"],
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "me": "GET /auth/me"
            },
            "contracts": {
                "upload": "POST /upload",
                "extract_sla": "POST /contract/{id}/extract-sla",
                "compare": "POST /contracts/compare"
            },
            "vehicles": {
                "vehicle_info": "GET /vehicle/{vin}",
                "vehicle_recalls": "GET /vehicle/{vin}/recalls",
                "complete_vehicle": "GET /vehicle/{vin}/complete"
            },
            "ai": {
                "negotiate": "POST /negotiate/{vin}",
                "chat": "POST /chat"
            },
            "conversations": {
                "list": "GET /conversations",
                "get": "GET /conversations/{id}",
                "create": "POST /conversations/create"
            },
            "demo": "GET /demo"
        }
    }


@app.post("/upload")
async def upload_contract(
    vin: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a contract PDF/image file for a specific VIN.
    Automatically fetches NHTSA vehicle data if this is a new VIN.
    """
    vin = vin.upper().strip()
    json_path = f"{DATA_DIR}/{vin}.json"

    # Fetch NHTSA vehicle data if this is a new VIN
    vehicle_info = None
    if not os.path.exists(json_path):
        try:
            vehicle_info = fetch_vehicle_data(vin)
        except Exception as e:
            vehicle_info = {"error": f"Failed to fetch NHTSA data: {str(e)}"}
        
        # Create JSON file with VIN and NHTSA data
        with open(json_path, "w") as f:
            json.dump({
                "vin": vin, 
                "nhtsa_vehicle_info": vehicle_info,
                "documents": []
            }, f, indent=2)

    # Save uploaded file
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1]
    file_path = f"{UPLOAD_DIR}/{file_id}.{ext}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extract text using OCR
    text = extract_text(file_path)

    # Store document info
    record = {
        "contract_id": file_id,
        "filename": file.filename,
        "file_path": file_path,
        "ocr_text": text,
        "uploaded_at": str(uuid.uuid1().time),
        "sla_extracted": False
    }

    # Update JSON file
    with open(json_path, "r+") as f:
        data = json.load(f)
        data["documents"].append(record)
        f.seek(0)
        json.dump(data, f, indent=2)

    return {
        "vin": vin,
        "contract_id": file_id,
        "filename": file.filename,
        "nhtsa_fetched": vehicle_info is not None,
        "status": "uploaded"
    }


@app.get("/vehicle/{vin}")
async def get_vehicle_info(vin: str):
    """
    Retrieve vehicle information from NHTSA API using VIN
    """
    try:
        vin = vin.upper().strip()
        vehicle_data = fetch_vehicle_data(vin)
        
        # Check if we have documents for this VIN
        json_path = f"{DATA_DIR}/{vin}.json"
        has_documents = os.path.exists(json_path)
        
        return {
            "vin": vin,
            "vehicle_info": vehicle_data,
            "has_documents": has_documents,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vehicle/{vin}/documents")
async def get_vehicle_documents(vin: str):
    """
    Retrieve all documents for a specific VIN
    """
    vin = vin.upper().strip()
    json_path = f"{DATA_DIR}/{vin}.json"
    
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="No documents found for this VIN")
    
    with open(json_path, "r") as f:
        data = json.load(f)
    
    return data


@app.post("/negotiate/{vin}")
async def negotiate_price(vin: str, user_query: str = Form("")):
    """
    AI-powered price negotiation chatbot
    Analyzes vehicle data, recalls, and contract details to provide negotiation advice
    """
    try:
        vin = vin.upper().strip()
        
        # Get complete vehicle data from JSON storage
        complete_data = fetch_complete_vehicle_data(vin)
        
        # Get documents if available
        json_path = f"{DATA_DIR}/{vin}.json"
        documents = []
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
                documents = data.get("documents", [])
        
        # Prepare data for LLM
        vehicle_data = {
            "vin": vin,
            "vehicle_info": complete_data.get("vehicle_data", {}),
            "recalls": complete_data.get("recalls", []),
            "documents": documents
        }
        
        # Get LLM service and generate negotiation advice
        llm_service = get_llm_service()
        result = llm_service.negotiate_price(vehicle_data, user_query)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contract/{contract_id}/extract-sla")
async def extract_sla_from_contract(contract_id: str):
    """
    Extract SLA parameters from contract using AI
    Returns 11 required parameters plus Contract Fairness Score (0-100)
    """
    json_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    
    for json_file in json_files:
        json_path = os.path.join(DATA_DIR, json_file)
        with open(json_path, "r") as f:
            data = json.load(f)
            for doc in data.get("documents", []):
                # Check both contract_id and document_id for compatibility
                doc_id = doc.get("contract_id") or doc.get("document_id")
                if doc_id == contract_id:
                    # Get contract text
                    contract_text = doc.get("ocr_text", "")
                    
                    if not contract_text:
                        raise HTTPException(
                            status_code=400, 
                            detail="No OCR text available for this contract"
                        )
                    
                    # Check if Tesseract error
                    if "Tesseract OCR not installed" in contract_text:
                        raise HTTPException(
                            status_code=400, 
                            detail="OCR extraction failed - Tesseract not installed"
                        )
                    
                    # Prepare vehicle data
                    vehicle_data = {
                        "vin": data.get("vin"),
                        "vehicle_info": data.get("nhtsa_vehicle_info", {})
                    }
                    
                    # Extract SLA using LLM
                    llm_service = get_llm_service()
                    sla_result = llm_service.extract_sla(vehicle_data, contract_text)
                    
                    # Update document with SLA data
                    if sla_result.get("status") == "success":
                        doc["sla_extracted"] = True
                        doc["sla_data"] = sla_result.get("sla_extraction")
                        
                        # Save updated data
                        with open(json_path, "w") as f_write:
                            json.dump(data, f_write, indent=2)
                    
                    return {
                        "contract_id": contract_id,
                        "vin": data.get("vin"),
                        "filename": doc.get("filename"),
                        "sla_extracted": True,
                        "sla_data": sla_result.get("sla_extraction"),
                        "vehicle_info": data.get("nhtsa_vehicle_info")
                    }
    
    raise HTTPException(status_code=404, detail="Contract not found")


@app.get("/vehicle/{vin}/recalls")
async def get_recalls(vin: str):
    """
    Get vehicle recalls from NHTSA
    """
    try:
        vin = vin.upper().strip()
        recalls = fetch_vehicle_recalls(vin)
        return {
            "vin": vin,
            "recalls": recalls,
            "count": len(recalls) if isinstance(recalls, list) else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vehicle/{vin}/complete")
async def get_complete_vehicle_data(vin: str):
    """
    Get complete vehicle data: NHTSA info + recalls + documents
    """
    try:
        vin = vin.upper().strip()
        
        # Get vehicle data and recalls
        complete_data = fetch_complete_vehicle_data(vin)
        
        # Get documents if available
        json_path = f"{DATA_DIR}/{vin}.json"
        documents = []
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
                documents = data.get("documents", [])
        
        return {
            "vin": vin,
            "vehicle_info": complete_data.get("vehicle_data"),
            "recalls": complete_data.get("recalls"),
            "documents": documents,
            "document_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/auth/register")
async def register(user: UserRegister):
    """Register a new user"""
    result = create_user(user.username, user.email, user.password)
    if result is None:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User created successfully", "user": result}


@app.post("/auth/login")
async def login(user: UserLogin):
    """Login and get access token"""
    authenticated_user = authenticate_user(user.username, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }


@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    contracts = get_user_contracts(current_user["username"])
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "contract_count": len(contracts),
        "contracts": contracts
    }


# ==================== CONVERSATION ENDPOINTS ====================

@app.post("/conversations/create")
async def create_new_conversation(
    vin: str = Form(...),
    title: str = Form("New Conversation"),
    current_user: dict = Depends(get_current_user)
):
    """Create a new conversation thread"""
    conversation_id = create_conversation(current_user["username"], vin, title)
    return {
        "conversation_id": conversation_id,
        "vin": vin,
        "title": title
    }


@app.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """Get all conversations for current user"""
    conversations = get_user_conversations(current_user["username"])
    return {"conversations": conversations}


@app.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific conversation with all messages"""
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify ownership
    if conversation["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return conversation


@app.post("/chat")
async def chat_with_history(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with AI using conversation history
    Multi-turn conversation support
    """
    try:
        conversation_id = message.conversation_id
        
        # If no conversation ID, we need a VIN from the message
        if not conversation_id:
            # For demo, extract VIN from message or use default
            raise HTTPException(
                status_code=400,
                detail="conversation_id required. Create conversation first with POST /conversations/create"
            )
        
        # Get conversation
        conversation = get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Verify ownership
        if conversation["user_id"] != current_user["username"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Add user message
        add_message(conversation_id, "user", message.message)
        
        # Get conversation context
        context = get_conversation_context(conversation_id)
        
        # Get vehicle data
        vin = conversation["vin"]
        complete_data = fetch_complete_vehicle_data(vin)
        
        json_path = f"{DATA_DIR}/{vin}.json"
        documents = []
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
                documents = data.get("documents", [])
        
        vehicle_data = {
            "vin": vin,
            "vehicle_info": complete_data.get("vehicle_data", {}),
            "recalls": complete_data.get("recalls", []),
            "documents": documents
        }
        
        # Build query with context
        full_query = f"Previous conversation:\n{context}\n\nCurrent question: {message.message}"
        
        # Get AI response
        llm_service = get_llm_service()
        result = llm_service.negotiate_price(vehicle_data, full_query)
        
        if result.get("status") == "success":
            ai_response = result.get("negotiation_advice")
            
            # Add assistant message
            add_message(conversation_id, "assistant", ai_response)
            
            return {
                "conversation_id": conversation_id,
                "response": ai_response,
                "vin": vin
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "AI service error"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONTRACT COMPARISON ENDPOINTS ====================

@app.post("/contracts/compare")
async def compare_multiple_contracts(
    request: CompareRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare multiple contracts side-by-side
    Requires 2-3 contract IDs
    """
    if len(request.contract_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 contracts to compare")
    
    if len(request.contract_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 contracts can be compared")
    
    comparison = compare_contracts(request.contract_ids)
    return comparison


@app.get("/contracts/{contract_id}/summary")
async def get_contract_summary_endpoint(contract_id: str):
    """Get contract summary for display"""
    summary = get_contract_summary(contract_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Contract not found")
    return summary


# ==================== DEMO WEB UI ====================

@app.get("/demo", response_class=HTMLResponse)
async def demo_ui():
    """Demo web interface for testing all features"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Car Lease AI Assistant - Demo</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .tabs {
                display: flex;
                background: #f5f5f5;
                border-bottom: 2px solid #ddd;
            }
            .tab {
                flex: 1;
                padding: 15px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                border: none;
                background: none;
                font-size: 1em;
                font-weight: 500;
            }
            .tab:hover {
                background: #e0e0e0;
            }
            .tab.active {
                background: white;
                color: #667eea;
                border-bottom: 3px solid #667eea;
            }
            .tab-content {
                display: none;
                padding: 30px;
            }
            .tab-content.active {
                display: block;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
                color: #333;
            }
            .form-group input, .form-group textarea, .form-group select {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 1em;
                transition: border 0.3s;
            }
            .form-group input:focus, .form-group textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 500;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            button:active {
                transform: translateY(0);
            }
            .result {
                margin-top: 20px;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                white-space: pre-wrap;
                max-height: 500px;
                overflow-y: auto;
            }
            .success { color: #4caf50; }
            .error { color: #f44336; }
            .chat-container {
                border: 2px solid #ddd;
                border-radius: 8px;
                height: 400px;
                overflow-y: auto;
                padding: 15px;
                margin-bottom: 15px;
                background: #fafafa;
            }
            .message {
                margin-bottom: 15px;
                padding: 12px;
                border-radius: 8px;
                max-width: 80%;
            }
            .message.user {
                background: #667eea;
                color: white;
                margin-left: auto;
            }
            .message.assistant {
                background: #f0f0f0;
                color: #333;
            }
            .auth-status {
                padding: 10px 20px;
                background: #f0f0f0;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .contract-card {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                transition: transform 0.2s;
            }
            .contract-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Car Lease AI Assistant</h1>
                <p>AI-Powered Contract Analysis & Negotiation Platform</p>
            </div>
            
            <div class="auth-status" id="authStatus">
                <span id="authText">Not logged in</span>
                <div id="authButtons"></div>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('auth')">🔐 Login/Register</button>
                <button class="tab" onclick="switchTab('upload')">📤 Upload Contract</button>
                <button class="tab" onclick="switchTab('chat')">💬 AI Negotiation Chat</button>
                <button class="tab" onclick="switchTab('compare')">⚖️ Compare Contracts</button>
                <button class="tab" onclick="switchTab('contracts')">📋 My Contracts</button>
            </div>
            
            <!-- Auth Tab -->
            <div id="auth" class="tab-content active">
                <h2>Authentication</h2>
                <div style="display: flex; gap: 30px;">
                    <div style="flex: 1;">
                        <h3>Register</h3>
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="text" id="regUsername" placeholder="Enter username">
                        </div>
                        <div class="form-group">
                            <label>Email:</label>
                            <input type="email" id="regEmail" placeholder="Enter email">
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="regPassword" placeholder="Enter password">
                        </div>
                        <button onclick="register()">Register</button>
                    </div>
                    <div style="flex: 1;">
                        <h3>Login</h3>
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="text" id="loginUsername" placeholder="Enter username">
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="loginPassword" placeholder="Enter password">
                        </div>
                        <button onclick="login()">Login</button>
                    </div>
                </div>
                <div id="authResult" class="result" style="display:none;"></div>
            </div>
            
            <!-- Upload Tab -->
            <div id="upload" class="tab-content">
                <h2>Upload Contract</h2>
                <div class="form-group">
                    <label>VIN:</label>
                    <input type="text" id="uploadVin" placeholder="1HGCM82633A004352">
                </div>
                <div class="form-group">
                    <label>Contract PDF:</label>
                    <input type="file" id="uploadFile" accept=".pdf,image/*">
                </div>
                <button onclick="uploadContract()">Upload & Extract</button>
                <div id="uploadResult" class="result" style="display:none;"></div>
            </div>
            
            <!-- Chat Tab -->
            <div id="chat" class="tab-content">
                <h2>AI Negotiation Assistant</h2>
                <div class="form-group">
                    <label>VIN:</label>
                    <input type="text" id="chatVin" placeholder="1HGCM82633A004352" value="1HGCM82633A004352">
                </div>
                <div class="form-group">
                    <label>Conversation:</label>
                    <select id="conversationSelect">
                        <option value="">New Conversation</option>
                    </select>
                    <button onclick="createConversation()" style="margin-top: 10px;">Create New Conversation</button>
                    <button onclick="loadConversations()" style="margin-top: 10px;">Refresh Conversations</button>
                </div>
                <div class="chat-container" id="chatMessages"></div>
                <div class="form-group">
                    <textarea id="chatMessage" rows="3" placeholder="Ask about negotiation strategies..."></textarea>
                </div>
                <button onclick="sendMessage()">Send Message</button>
            </div>
            
            <!-- Compare Tab -->
            <div id="compare" class="tab-content">
                <h2>Compare Contracts</h2>
                <p>Enter 2-3 contract IDs to compare side-by-side:</p>
                <div class="form-group">
                    <label>Contract ID 1:</label>
                    <input type="text" id="compareId1" placeholder="f5d511dc-4083-4892-ad51-b6e89a3b2ff1">
                </div>
                <div class="form-group">
                    <label>Contract ID 2:</label>
                    <input type="text" id="compareId2">
                </div>
                <div class="form-group">
                    <label>Contract ID 3 (optional):</label>
                    <input type="text" id="compareId3">
                </div>
                <button onclick="compareContracts()">Compare Contracts</button>
                <div id="compareResult" class="result" style="display:none;"></div>
            </div>
            
            <!-- Contracts Tab -->
            <div id="contracts" class="tab-content">
                <h2>My Contracts</h2>
                <button onclick="loadMyContracts()">Load My Contracts</button>
                <div id="contractsList"></div>
            </div>
        </div>
        
        <script>
            let authToken = localStorage.getItem('authToken');
            let currentUsername = localStorage.getItem('username');
            let currentConversationId = null;
            
            // Update auth status
            function updateAuthStatus() {
                const authText = document.getElementById('authText');
                const authButtons = document.getElementById('authButtons');
                
                if (authToken) {
                    authText.textContent = `Logged in as: ${currentUsername}`;
                    authButtons.innerHTML = '<button onclick="logout()">Logout</button>';
                } else {
                    authText.textContent = 'Not logged in';
                    authButtons.innerHTML = '';
                }
            }
            
            function switchTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
            }
            
            async function register() {
                const username = document.getElementById('regUsername').value;
                const email = document.getElementById('regEmail').value;
                const password = document.getElementById('regPassword').value;
                
                try {
                    const response = await fetch('/auth/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, email, password })
                    });
                    
                    const data = await response.json();
                    const result = document.getElementById('authResult');
                    result.style.display = 'block';
                    
                    if (response.ok) {
                        result.className = 'result success';
                        result.textContent = 'Registration successful! Please login.';
                    } else {
                        result.className = 'result error';
                        result.textContent = 'Error: ' + data.detail;
                    }
                } catch (error) {
                    document.getElementById('authResult').style.display = 'block';
                    document.getElementById('authResult').textContent = 'Error: ' + error.message;
                }
            }
            
            async function login() {
                const username = document.getElementById('loginUsername').value;
                const password = document.getElementById('loginPassword').value;
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    
                    const data = await response.json();
                    const result = document.getElementById('authResult');
                    result.style.display = 'block';
                    
                    if (response.ok) {
                        authToken = data.access_token;
                        currentUsername = data.username;
                        localStorage.setItem('authToken', authToken);
                        localStorage.setItem('username', currentUsername);
                        
                        result.className = 'result success';
                        result.textContent = 'Login successful!';
                        updateAuthStatus();
                    } else {
                        result.className = 'result error';
                        result.textContent = 'Error: ' + data.detail;
                    }
                } catch (error) {
                    document.getElementById('authResult').textContent = 'Error: ' + error.message;
                }
            }
            
            function logout() {
                localStorage.removeItem('authToken');
                localStorage.removeItem('username');
                authToken = null;
                currentUsername = null;
                updateAuthStatus();
                alert('Logged out successfully');
            }
            
            async function uploadContract() {
                const vin = document.getElementById('uploadVin').value;
                const fileInput = document.getElementById('uploadFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('vin', vin);
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    const result = document.getElementById('uploadResult');
                    result.style.display = 'block';
                    result.textContent = JSON.stringify(data, null, 2);
                    
                    // Extract SLA automatically
                    if (data.contract_id) {
                        await extractSLA(data.contract_id);
                    }
                } catch (error) {
                    document.getElementById('uploadResult').textContent = 'Error: ' + error.message;
                }
            }
            
            async function extractSLA(contractId) {
                try {
                    const response = await fetch(`/contract/${contractId}/extract-sla`, {
                        method: 'POST'
                    });
                    
                    const data = await response.json();
                    const result = document.getElementById('uploadResult');
                    result.textContent += '\\n\\n=== SLA EXTRACTION ===\\n' + JSON.stringify(data, null, 2);
                } catch (error) {
                    console.error('SLA extraction error:', error);
                }
            }
            
            async function createConversation() {
                if (!authToken) {
                    alert('Please login first');
                    return;
                }
                
                const vin = document.getElementById('chatVin').value;
                
                try {
                    const formData = new FormData();
                    formData.append('vin', vin);
                    formData.append('title', `Negotiation for ${vin}`);
                    
                    const response = await fetch('/conversations/create', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        },
                        body: formData
                    });
                    
                    const data = await response.json();
                    currentConversationId = data.conversation_id;
                    alert(`Conversation created: ${currentConversationId}`);
                    loadConversations();
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            async function loadConversations() {
                if (!authToken) return;
                
                try {
                    const response = await fetch('/conversations', {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });
                    
                    const data = await response.json();
                    const select = document.getElementById('conversationSelect');
                    select.innerHTML = '<option value="">New Conversation</option>';
                    
                    data.conversations.forEach(conv => {
                        const option = document.createElement('option');
                        option.value = conv.conversation_id;
                        option.textContent = `${conv.title} (${conv.message_count} messages)`;
                        select.appendChild(option);
                    });
                } catch (error) {
                    console.error('Error loading conversations:', error);
                }
            }
            
            async function sendMessage() {
                if (!authToken) {
                    alert('Please login first');
                    return;
                }
                
                const message = document.getElementById('chatMessage').value;
                const conversationId = document.getElementById('conversationSelect').value || currentConversationId;
                
                if (!conversationId) {
                    alert('Please create a conversation first');
                    return;
                }
                
            try {
                    // Display user message
                    const chatMessages = document.getElementById('chatMessages');
                    const userMsg = document.createElement('div');
                    userMsg.className = 'message user';
                    userMsg.textContent = message;
                    chatMessages.appendChild(userMsg);
                    
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            message: message,
                            conversation_id: conversationId
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Display assistant message
                    const assistantMsg = document.createElement('div');
                    assistantMsg.className = 'message assistant';
                    assistantMsg.textContent = data.response;
                    chatMessages.appendChild(assistantMsg);
                    
                    // Scroll to bottom
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    
                    // Clear input
                    document.getElementById('chatMessage').value = '';
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            async function compareContracts() {
                const id1 = document.getElementById('compareId1').value;
                const id2 = document.getElementById('compareId2').value;
                const id3 = document.getElementById('compareId3').value;
                
                const contract_ids = [id1, id2];
                if (id3) contract_ids.push(id3);
                
                if (!authToken) {
                    alert('Please login first');
                    return;
                }
                
                try {
                    const response = await fetch('/contracts/compare', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ contract_ids })
                    });
                    
                    const data = await response.json();
                    const result = document.getElementById('compareResult');
                    result.style.display = 'block';
                    result.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    document.getElementById('compareResult').textContent = 'Error: ' + error.message;
                }
            }
            
            async function loadMyContracts() {
                if (!authToken) {
                    alert('Please login first');
                    return;
                }
                
                try {
                    const response = await fetch('/auth/me', {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });
                    
                    const data = await response.json();
                    const list = document.getElementById('contractsList');
                    list.innerHTML = '<h3>Your Contracts:</h3>';
                    
                    if (data.contracts && data.contracts.length > 0) {
                        data.contracts.forEach(contract => {
                            const card = document.createElement('div');
                            card.className = 'contract-card';
                            card.innerHTML = `
                                <strong>VIN:</strong> ${contract.vin}<br>
                                <strong>Contract ID:</strong> ${contract.contract_id}
                            `;
                            list.appendChild(card);
                        });
                    } else {
                        list.innerHTML += '<p>No contracts uploaded yet.</p>';
                    }
                } catch (error) {
                    document.getElementById('contractsList').innerHTML = 'Error: ' + error.message;
                }
            }
            
            // Initialize
            updateAuthStatus();
            if (authToken) {
                loadConversations();
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)