"""
AJAX AI - MVC Controller: Chat & Conversation Endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from models.schemas import ChatRequest, ChatResponse
from core.router import router
from controllers.auth_controller import require_authenticated_user
from database.crud import (
    create_conversation,
    get_conversation,
    list_conversations,
    get_conversation_messages,
    delete_conversation
)

chat_router = APIRouter(prefix="/api", tags=["Chat & Intelligence"])

@chat_router.post("/chat", response_model=ChatResponse)
async def process_chat_message(req: ChatRequest, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    conv_id = req.conversation_id or create_conversation("API Chat", user_id=current_user["id"])
    if req.conversation_id and not get_conversation(conv_id, user_id=current_user["id"]):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found.")
    result = router.process_query(
        req.query,
        conv_id,
        modality=req.modality or "api",
        web_search=bool(req.web_search),
        language=req.language or "en",
        user_id=current_user["id"]
    )
    return JSONResponse(content=result, status_code=200)

@chat_router.post("/chat/stream")
async def process_chat_message_stream(req: ChatRequest, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Server-Sent Events (SSE) real-time token streaming endpoint."""
    conv_id = req.conversation_id or create_conversation("Web Chat", user_id=current_user["id"])
    if req.conversation_id and not get_conversation(conv_id, user_id=current_user["id"]):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return StreamingResponse(
        router.process_query_stream(
            req.query,
            conv_id,
            modality=req.modality or "web_stream",
            web_search=bool(req.web_search),
            language=req.language or "en",
            user_id=current_user["id"]
        ),
        media_type="text/event-stream"
    )

@chat_router.get("/conversations")
async def get_all_conversations(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Retrieve recent chat sessions for sidebar history."""
    convs = list_conversations(limit=40, user_id=current_user["id"])
    return {"conversations": convs}

@chat_router.get("/conversations/{conv_id}")
async def get_conversation_history(conv_id: str, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Retrieve full message history for a specific conversation session."""
    if not get_conversation(conv_id, user_id=current_user["id"]):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found.")
    messages = get_conversation_messages(conv_id, limit=100, user_id=current_user["id"])
    return {"conversation_id": conv_id, "messages": messages}

@chat_router.delete("/conversations/{conv_id}")
async def remove_conversation(conv_id: str, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Delete a conversation session and all its messages."""
    success = delete_conversation(conv_id, user_id=current_user["id"])
    return {"success": success, "conversation_id": conv_id}

