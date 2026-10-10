"""
AJAX AI - MVC Controller: Memory Management
"""

from fastapi import APIRouter, HTTPException
from models.schemas import MemoryRequest
from database.crud import save_memory, search_memories

memory_router = APIRouter(prefix="/api", tags=["Memory & Personalization"])

@memory_router.get("/memory")
async def get_memories():
    mems = search_memories(limit=20)
    return {"memories": mems}

@memory_router.post("/memory")
async def store_memory(req: MemoryRequest):
    if req.key and req.value:
        mem_id = save_memory(key_text=req.key, value_text=req.value, category=req.category or "general")
        return {"success": True, "memory_id": mem_id}
    raise HTTPException(status_code=400, detail="Missing key or value")
