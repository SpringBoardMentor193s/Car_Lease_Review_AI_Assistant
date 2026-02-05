"""
Authentication service for user management
Implements JWT-based authentication
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import json

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple file-based user storage (replace with database in production)
USERS_FILE = "users.json"


def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def verify_password(plain_password, hashed_password):
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def authenticate_user(username: str, password: str):
    """Authenticate user with username and password"""
    users = load_users()
    if username not in users:
        return False
    user = users[username]
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_user(username: str, email: str, password: str):
    """Create a new user"""
    users = load_users()
    
    # Check if user already exists
    if username in users:
        return None
    
    # Create user
    hashed_password = get_password_hash(password)
    users[username] = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "contracts": []
    }
    
    save_users(users)
    return {"username": username, "email": email}


def get_user(username: str):
    """Get user by username"""
    users = load_users()
    if username not in users:
        return None
    user = users[username].copy()
    user.pop("hashed_password", None)  # Don't return password hash
    return user


def get_user_contracts(username: str):
    """Get all contracts for a user"""
    users = load_users()
    if username not in users:
        return []
    return users[username].get("contracts", [])


def add_user_contract(username: str, vin: str, contract_id: str):
    """Link a contract to a user"""
    users = load_users()
    if username not in users:
        return False
    
    if "contracts" not in users[username]:
        users[username]["contracts"] = []
    
    # Avoid duplicates
    contract_ref = {"vin": vin, "contract_id": contract_id}
    if contract_ref not in users[username]["contracts"]:
        users[username]["contracts"].append(contract_ref)
        save_users(users)
    
    return True
