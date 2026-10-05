"""
AJAX AI - Context Manager
Assembles dynamic context from conversation history, persistent memories, and RAG knowledge.
"""

from typing import List, Dict, Any, Optional
from database.crud import get_conversation_messages, search_memories
from core.prompts import format_system_prompt

class ContextManager:
    def __init__(self, max_history_turns: int = 10):
        self.max_history_turns = max_history_turns

    def build_context(
        self,
        conversation_id: str,
        current_query: str,
        rag_context: str = ""
    ) -> List[Dict[str, str]]:
        # 1. Fetch relevant memories
        memories = search_memories(query=current_query, limit=5)
        memories_str = ""
        if memories:
            memories_str = "\n".join([f"- {m['key_text']}: {m['value_text']}" for m in memories])

        # 2. Build system prompt
        system_prompt = format_system_prompt(memories_context=memories_str, rag_context=rag_context)
        
        messages = [{"role": "system", "content": system_prompt}]

        # 3. Retrieve recent conversation history
        history = get_conversation_messages(conversation_id, limit=self.max_history_turns)
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # 4. Append current user query if not already present
        if not history or history[-1]["content"] != current_query or history[-1]["role"] != "user":
            messages.append({
                "role": "user",
                "content": current_query
            })

        return messages

context_manager = ContextManager()
