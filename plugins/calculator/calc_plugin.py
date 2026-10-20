"""
AJAX AI - Scientific Calculator Plugin
"""

import math
from typing import List
from plugins.base import BasePlugin
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory

class ScientificCalcTool(BaseTool):
    name = "scientific_calculate"
    description = "Compute advanced math formulas including trigonometry, exponents, logarithms, and square roots."
    category = ToolCategory.CUSTOM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["sqrt", "sin", "cos", "tan", "log", "exp", "factorial"]},
            "value": {"type": "number", "description": "Numeric operand"}
        },
        "required": ["operation", "value"]
    }

    def execute(self, operation: str, value: float, **kwargs) -> ToolResult:
        try:
            val = float(value)
            op = operation.lower().strip()
            if op == "sqrt":
                if val < 0:
                    return ToolResult(success=False, output=None, error="Square root of negative number is not real.")
                res = math.sqrt(val)
            elif op == "sin":
                res = math.sin(math.radians(val))
            elif op == "cos":
                res = math.cos(math.radians(val))
            elif op == "tan":
                res = math.tan(math.radians(val))
            elif op == "log":
                if val <= 0:
                    return ToolResult(success=False, output=None, error="Logarithm undefined for non-positive numbers.")
                res = math.log10(val)
            elif op == "exp":
                res = math.exp(val)
            elif op == "factorial":
                if val < 0 or int(val) != val:
                    return ToolResult(success=False, output=None, error="Factorial only defined for non-negative integers.")
                res = math.factorial(int(val))
            else:
                return ToolResult(success=False, output=None, error=f"Unknown operation: {operation}")

            return ToolResult(success=True, output=f"{operation}({val}) = {res}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Calculation error: {e}")

class CalculatorPlugin(BasePlugin):
    def on_load(self) -> bool:
        return True

    def on_unload(self) -> bool:
        return True

    def get_tools(self) -> List[BaseTool]:
        return [ScientificCalcTool()]
