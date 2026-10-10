"""
AJAX AI - Document Query (RAG) Tool
Enables querying indexed project or local documents.
"""

from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from ai.rag.store import rag_store

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
        results = rag_store.query(query, top_k=3)
        if not results:
            return ToolResult(success=True, output="No matching information found in indexed documents.")

        formatted = []
        for i, res in enumerate(results, 1):
            formatted.append(f"[{i}] Source: {res['source']}\n{res['chunk']}")

        output = "Relevant context from documents:\n\n" + "\n\n---\n\n".join(formatted)
        return ToolResult(success=True, output=output, metadata={"results": results})
