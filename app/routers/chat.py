from fastapi import APIRouter
from app import models
from app.services import llm_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post("/", response_model=models.ChatResponse)
def chat(request: models.ChatRequest):
    # Retrieve context from DB if needed using request.context ID
    # For now, simplistic pass-through
    response = llm_service.llm_service.chat_response(request.message, {})
    return {"response": response}
