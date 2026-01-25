from fastapi import FastAPI
from pydantic import BaseModel

# Import your existing logic
from backend.pipeline.process_contract import process_contract
from backend.llm.negotiation_chatbot import negotiation_chat

app = FastAPI(title = "Car Lease AI Assistant")

# ---------- Request Schemas ----------

class ContractRequest(BaseModel):
    pdf_path: str


class ChatRequest(BaseModel):
    sla_data: dict
    user_message: str


# ---------- Health Check ----------

@app.get("/")
def health():
    return {"status": "Backend running successfully"}


# ---------- Contract Processing API ----------

@app.post("/process-contract")
def process_contract_api(request: ContractRequest):
    """
    Takes a PDF path, runs OCR + LLM + VIN pipeline,
    and returns structured contract analysis.
    """
    result = process_contract(request.pdf_path)
    return result


# ---------- Negotiation Chatbot API ----------

@app.post("/chat")
def chat_api(request: ChatRequest):
    """
    Takes extracted SLA data + user message
    and returns AI-powered negotiation advice.
    """
    reply = negotiation_chat(
        request.sla_data,
        request.user_message
    )
    return {"response": reply}
