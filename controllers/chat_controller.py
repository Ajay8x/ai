"""
AJAX AI - MVC Controller: Chat & Conversation Endpoints
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models.schemas import ChatRequest, ChatResponse
from core.router import router
from database.crud import create_conversation

chat_router = APIRouter(prefix="/api", tags=["Chat & Intelligence"])

@chat_router.post("/chat", response_model=ChatResponse)
async def process_chat_message(req: ChatRequest):
    conv_id = req.conversation_id or create_conversation("API Chat")
    result = router.process_query(req.query, conv_id, modality=req.modality or "api")
    return JSONResponse(content=result, status_code=200)
