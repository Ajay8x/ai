"""
AJAX AI - Document Query (RAG) Tool
Enables querying indexed project or local documents.
"""

from typing import Dict, Any, Optional
import os
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from ai.rag.store import rag_store
from database.db import SYSTEM_SCOPE

class QueryDocumentsTool(BaseTool):
    name = "query_documents"
    description = "Search and extract answers ONLY from user-uploaded PDF or custom documents. Do NOT use for general knowledge questions."
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Question or keywords to search across documents"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> ToolResult:
        results = rag_store.query(query, top_k=3, user_id=kwargs.get("user_id") or SYSTEM_SCOPE)
        if not results:
            return ToolResult(success=True, output="No matching information found in indexed documents.")

        formatted = []
        for i, res in enumerate(results, 1):
            citation = res.get("citation") or f"{res.get('title', 'Document')} — {os.path.basename(res.get('source', ''))}"
            score = res.get("score", 0.0)
            formatted.append(f"[{i}] {citation} (relevance: {score:.4f})\n{res['chunk']}")

        output = "Relevant context from documents:\n\n" + "\n\n---\n\n".join(formatted)
        return ToolResult(success=True, output=output, metadata={"results": results})
