"""
AJAX AI - Base Tool Framework
Standardized structure for all executable actions and tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from core.permissions import PermissionLevel, ToolCategory

@dataclass
class ToolResult:
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }

class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool description"
    category: ToolCategory = ToolCategory.CUSTOM
    permission: PermissionLevel = PermissionLevel.SAFE
    parameters_schema: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool action."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to OpenAI/LLM tool calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
