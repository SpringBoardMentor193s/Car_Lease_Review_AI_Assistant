"""
Conversation history service for multi-turn chat
Stores and retrieves conversation threads
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional


CONVERSATIONS_DIR = "conversations"
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)


def create_conversation(user_id: str, vin: str, title: str = "New Conversation") -> str:
    """Create a new conversation thread"""
    conversation_id = str(uuid.uuid4())
    
    conversation = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "vin": vin,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": []
    }
    
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(filepath, "w") as f:
        json.dump(conversation, f, indent=2)
    
    return conversation_id


def get_conversation(conversation_id: str) -> Optional[Dict]:
    """Get a conversation by ID"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "r") as f:
        return json.load(f)


def add_message(conversation_id: str, role: str, content: str) -> bool:
    """Add a message to a conversation"""
    conversation = get_conversation(conversation_id)
    
    if not conversation:
        return False
    
    message = {
        "role": role,  # "user" or "assistant"
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    conversation["messages"].append(message)
    conversation["updated_at"] = datetime.utcnow().isoformat()
    
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(filepath, "w") as f:
        json.dump(conversation, f, indent=2)
    
    return True


def get_user_conversations(user_id: str) -> List[Dict]:
    """Get all conversations for a user"""
    conversations = []
    
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            with open(filepath, "r") as f:
                conv = json.load(f)
                if conv.get("user_id") == user_id:
                    # Return summary (without full message content)
                    conversations.append({
                        "conversation_id": conv["conversation_id"],
                        "vin": conv["vin"],
                        "title": conv["title"],
                        "created_at": conv["created_at"],
                        "updated_at": conv["updated_at"],
                        "message_count": len(conv["messages"])
                    })
    
    # Sort by updated_at (most recent first)
    conversations.sort(key=lambda x: x["updated_at"], reverse=True)
    return conversations


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    if not os.path.exists(filepath):
        return False
    
    os.remove(filepath)
    return True


def get_conversation_context(conversation_id: str, max_messages: int = 10) -> str:
    """Get conversation history as context for LLM"""
    conversation = get_conversation(conversation_id)
    
    if not conversation:
        return ""
    
    messages = conversation["messages"][-max_messages:]  # Last N messages
    
    context = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        context += f"{role}: {msg['content']}\n\n"
    
    return context
