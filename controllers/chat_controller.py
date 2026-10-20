"""
AJAX AI - MVC Controller: Chat & Conversation Endpoints
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from models.schemas import ChatRequest, ChatResponse
from core.router import router
from database.crud import (
    create_conversation,
    list_conversations,
    get_conversation_messages,
    delete_conversation
)

chat_router = APIRouter(prefix="/api", tags=["Chat & Intelligence"])

@chat_router.post("/chat", response_model=ChatResponse)
async def process_chat_message(req: ChatRequest):
    conv_id = req.conversation_id or create_conversation("API Chat")
    result = router.process_query(
        req.query,
        conv_id,
        modality=req.modality or "api",
        web_search=bool(req.web_search)
    )
    return JSONResponse(content=result, status_code=200)

@chat_router.post("/chat/stream")
async def process_chat_message_stream(req: ChatRequest):
    """Server-Sent Events (SSE) real-time token streaming endpoint."""
    conv_id = req.conversation_id or create_conversation("Web Chat")
    return StreamingResponse(
        router.process_query_stream(
            req.query,
            conv_id,
            modality=req.modality or "web_stream",
            web_search=bool(req.web_search)
        ),
        media_type="text/event-stream"
    )

@chat_router.get("/conversations")
async def get_all_conversations():
    """Retrieve recent chat sessions for sidebar history."""
    convs = list_conversations(limit=40)
    return {"conversations": convs}

@chat_router.get("/conversations/{conv_id}")
async def get_conversation_history(conv_id: str):
    """Retrieve full message history for a specific conversation session."""
    messages = get_conversation_messages(conv_id, limit=100)
    return {"conversation_id": conv_id, "messages": messages}

@chat_router.delete("/conversations/{conv_id}")
async def remove_conversation(conv_id: str):
    """Delete a conversation session and all its messages."""
    success = delete_conversation(conv_id)
    return {"success": success, "conversation_id": conv_id}

