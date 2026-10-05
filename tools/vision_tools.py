"""
AJAX AI - Vision Analysis Tool
"""

from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from ai.vision.screen import screen_vision

class AnalyzeScreenTool(BaseTool):
    name = "analyze_screen"
    description = "Capture the current desktop screen and analyze its contents or active application windows."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "focus_area": {"type": "string", "description": "Optional focus area (e.g. error, browser, code, general)", "default": "general"}
        }
    }

    def execute(self, focus_area: str = "general", **kwargs) -> ToolResult:
        res = screen_vision.capture_and_inspect()
        if res.get("success"):
            return ToolResult(
                success=True,
                output=f"Captured desktop screenshot ({res['resolution']}). Image saved for vision analysis at: {res['file_path']}",
                metadata=res
            )
        return ToolResult(success=False, output=None, error=res.get("error", "Screen capture failed."))
