"""
AJAX AI - Context Manager
Assembles dynamic context from conversation history, persistent memories, cross-session MongoDB records, and RAG knowledge.
"""

from typing import List, Dict, Any, Optional
from database.crud import get_conversation_messages, search_memories, get_cross_session_context
from database.db import SYSTEM_SCOPE
from core.prompts import format_system_prompt
from ai.rag.store import rag_store

class ContextManager:
    def __init__(self, max_history_turns: int = 10):
        self.max_history_turns = max_history_turns

    def build_context(
        self,
        conversation_id: str,
        current_query: str,
        rag_context: str = "",
        language: str = "en",
        intent_context: str = "",
        user_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        # 1. Fetch cross-session knowledge & memories from MongoDB Atlas
        cross_session_ctx = get_cross_session_context(
            query=current_query,
            user_id=user_id,
            current_conversation_id=conversation_id,
            limit=5
        )

        # 2. Retrieve relevant system and user-owned document chunks before
        # building the model context. The ownership scope is critical: a
        # logged-in user may see shared system documents and their own uploads,
        # but never another user's private RAG chunks.
        if not rag_context:
            try:
                rag_results = rag_store.query(
                    current_query,
                    top_k=4,
                    user_id=user_id or SYSTEM_SCOPE
                )
                if rag_results:
                    formatted_chunks = []
                    for index, result in enumerate(rag_results, 1):
                        citation = result.get("citation") or result.get("file_name") or "Uploaded document"
                        formatted_chunks.append(
                            f"[{index}] {citation}\n{result.get('chunk', '').strip()}"
                        )
                    rag_context = "\n\n---\n\n".join(formatted_chunks)
            except Exception:
                # RAG is an enrichment layer; a retrieval outage must not
                # prevent the normal chat experience from responding.
                rag_context = ""

        # 3. Build system prompt with language mode, neural intent, memory,
        # and the grounded document context assembled above.
        system_prompt = format_system_prompt(
            memories_context="",
            past_sessions_context=cross_session_ctx,
            rag_context=rag_context,
            language=language,
            intent_context=intent_context
        )
        
        messages = [{"role": "system", "content": system_prompt}]

        # 4. Retrieve recent conversation history for current session
        history = get_conversation_messages(conversation_id, limit=self.max_history_turns, user_id=user_id)
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
