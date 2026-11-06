"""
AJAX AI - MVC Controller: Memory Management
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from models.schemas import MemoryRequest
from controllers.auth_controller import require_authenticated_user
from memory.manager import memory_manager

memory_router = APIRouter(prefix="/api", tags=["Memory & Personalization"])

@memory_router.get("/memory")
async def get_memories(
    query: str = Query(default="", max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: Dict[str, Any] = Depends(require_authenticated_user)
):
    mems = memory_manager.recall(query=query, limit=limit, user_id=current_user["id"])
    return {"memories": mems}

@memory_router.post("/memory")
async def store_memory(req: MemoryRequest, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    result = memory_manager.remember_fact(
        key_text=req.key,
        value_text=req.value,
        category=req.category or "general",
        user_id=current_user["id"]
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Could not save memory."))
    return result

@memory_router.delete("/memory/{memory_id}")
async def forget_memory(memory_id: str, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    deleted = memory_manager.forget(memory_id, user_id=current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"success": True, "memory_id": memory_id}
