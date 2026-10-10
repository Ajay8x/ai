"""
AJAX AI - Central Tool Registry
Centralized registration, permission lookup, and execution dispatcher for all system tools.
"""

import time
from typing import Dict, List, Optional, Any
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel
from core.safety import safety_engine
from core.logger import tools_logger, error_logger
from database.crud import record_tool_execution

class ToolRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance.tools: Dict[str, BaseTool] = {}
        return cls._instance

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool
        tools_logger.info(f"Registered tool: '{tool.name}' [{tool.permission}]")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self.tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, parameters: Any = None, confirmed_by_user: bool = False) -> ToolResult:
        if isinstance(parameters, list):
            if parameters and isinstance(parameters[0], dict):
                parameters = parameters[0]
            else:
                parameters = {}
        elif not isinstance(parameters, dict):
            parameters = {}

        tool = self.get_tool(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found."
            error_logger.error(error_msg)
            return ToolResult(success=False, output=None, error=error_msg)

        # Safety & Permission check
        is_safe, reason = safety_engine.check_tool_permission(tool.permission, requires_user_ack=not confirmed_by_user)
        if not is_safe:
            return ToolResult(success=False, output=None, error=f"Tool execution blocked: {reason}")
        
        if reason == "CONFIRM_REQUIRED" and not confirmed_by_user:
            return ToolResult(
                success=False,
                output=None,
                error=f"Confirmation required: Action '{tool_name}' may modify system state or delete data.",
                metadata={"confirmation_needed": True, "tool": tool_name, "params": parameters}
            )

        start_time = time.time()
        try:
            result = tool.execute(**parameters)
            duration = (time.time() - start_time) * 1000
            status = "SUCCESS" if result.success else "ERROR"
            
            # Log execution
            tools_logger.info(f"Executed tool '{tool_name}' | Status: {status} | Duration: {duration:.2f}ms")
            record_tool_execution(tool_name, parameters, result.to_dict(), status, duration)
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Exception executing tool '{tool_name}': {str(e)}"
            error_logger.error(error_msg)
            record_tool_execution(tool_name, parameters, {"error": error_msg}, "ERROR", duration)
            return ToolResult(success=False, output=None, error=error_msg)

# Global Tool Registry
registry = ToolRegistry()
