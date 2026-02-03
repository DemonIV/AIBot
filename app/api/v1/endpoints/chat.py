from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from app.services.ai_service import AIService

router = APIRouter()

# Initialize AI Service once (or as a dependency) to keep memory alive
ai_service = AIService()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI Sales Assistant.
    Provide a session_id to maintain context. If none is provided, a new one is generated.
    """
    session_id = request.session_id or str(uuid.uuid4())
    response = await ai_service.generate_response(request.message, session_id)
    return ChatResponse(response=response, session_id=session_id)
