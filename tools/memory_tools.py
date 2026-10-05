"""
AJAX AI - Memory Tools
Provides memory saving, recalling, and deleting tools for the AI agent.
"""

from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from memory.manager import memory_manager

class RememberTool(BaseTool):
    name = "remember_fact"
    description = "Store a user preference, personal detail, or important note into long-term memory."
    category = ToolCategory.MEMORY
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Subject or topic to remember (e.g. user_name, favorite_editor, project_root)"},
            "value": {"type": "string", "description": "The exact information to remember"}
        },
        "required": ["key", "value"]
    }

    def execute(self, key: str, value: str, **kwargs) -> ToolResult:
        res = memory_manager.remember_fact(key_text=key, value_text=value)
        if res["success"]:
            return ToolResult(success=True, output=f"I have remembered that {key} is {value}.")
        return ToolResult(success=False, output=None, error=res.get("error", "Failed to remember."))

class RecallMemoryTool(BaseTool):
    name = "recall_memory"
    description = "Search long-term memory for previously remembered facts or notes."
    category = ToolCategory.MEMORY
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query or topic"}
        }
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        memories = memory_manager.recall(query=query, limit=10)
        if memories:
            formatted = "\n".join([f"- {m['key_text']}: {m['value_text']}" for m in memories])
            return ToolResult(success=True, output=f"Found memories:\n{formatted}", metadata={"memories": memories})
        return ToolResult(success=True, output="I don't have any matching memories saved.")
