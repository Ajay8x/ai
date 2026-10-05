"""
AJAX AI - Multi-Tier Memory Manager
Orchestrates Short-Term (Session), Long-Term (User facts), Episodic, and Semantic memory.
"""

from typing import List, Dict, Any, Optional
from collections import deque
from database.crud import save_memory, search_memories, delete_memory
from memory.privacy import privacy_filter
from core.logger import ajax_logger

class MemoryManager:
    def __init__(self, session_buffer_size: int = 20):
        # Short-term in-memory buffer
        self.short_term: deque = deque(maxlen=session_buffer_size)

    def add_short_term(self, role: str, content: str):
        self.short_term.append({"role": role, "content": content})

    def get_short_term(self) -> List[Dict[str, str]]:
        return list(self.short_term)

    def remember_fact(self, key_text: str, value_text: str, category: str = "user_fact") -> Dict[str, Any]:
        """Save a long-term memory with privacy inspection."""
        is_safe, reason = privacy_filter.is_safe_to_remember(f"{key_text} {value_text}")
        if not is_safe:
            ajax_logger.warning(f"Memory storage blocked by privacy filter: {reason}")
            return {"success": False, "error": f"Memory blocked: {reason}"}

        mem_id = save_memory(key_text=key_text, value_text=value_text, category=category)
        ajax_logger.info(f"Saved long-term memory [{category}]: '{key_text}' -> '{value_text}'")
        return {"success": True, "memory_id": mem_id, "key": key_text, "value": value_text}

    def recall(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        return search_memories(query=query, limit=limit)

    def forget(self, memory_id: str) -> bool:
        return delete_memory(memory_id)

memory_manager = MemoryManager()
