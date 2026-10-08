"""
AJAX AI - Instant Calculator Tool
Safely evaluates arithmetic expressions, percentages, powers, and math formulas with zero LLM latency.
"""

import ast
import math
import operator
import re
from typing import Dict, Any
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory

# Allowed safe operators and math functions
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
    "abs": abs,
    "round": round,
    "pi": math.pi,
    "e": math.e,
}

def safe_eval(node):
    """Safely evaluates an AST expression without arbitrary code execution."""
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    elif isinstance(node, ast.Constant): # Python 3.8+ numbers/strings
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            return ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported operator: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](safe_eval(node.operand))
        raise ValueError(f"Unsupported unary operator: {op_type}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ALLOWED_FUNCTIONS:
            func = ALLOWED_FUNCTIONS[node.func.id]
            args = [safe_eval(arg) for arg in node.args]
            return func(*args)
        raise ValueError("Unsupported function call")
    elif isinstance(node, ast.Name) and node.id in ALLOWED_FUNCTIONS:
        return ALLOWED_FUNCTIONS[node.id]
    else:
        raise TypeError(f"Unsupported expression element: {type(node)}")

class CalculatorTool(BaseTool):
    name = "calculate"
    description = "Safely evaluates math expressions, calculations, and percentages (e.g. '2+2', '15% of 800', 'sqrt(144)', '25 * 4')."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "The mathematical expression to evaluate (e.g. '2+2', '125*4')"}
        },
        "required": ["expression"]
    }

    def execute(self, expression: str = "", **kwargs) -> ToolResult:
        expr = expression.strip()
        if not expr:
            return ToolResult(success=False, output="", error="No mathematical expression provided.")

        # Handle 'X ka Y%' or 'X of Y%' pattern (e.g. '100 ka 10%', '500 ka 20 percent')
        hindi_pct = re.search(r"(\d+(?:\.\d+)?)\s*(?:ka|of)\s*(\d+(?:\.\d+)?)\s*(?:%|percent)", expr, flags=re.IGNORECASE)
        if hindi_pct:
            total_val = float(hindi_pct.group(1))
            pct_val = float(hindi_pct.group(2))
            res = (pct_val / 100.0) * total_val
            return ToolResult(
                success=True,
                output=f"{expr} = {res:g}",
                metadata={"result": res, "expression": expr}
            )

        # Handle 'X% of Y' pattern (e.g. '15% of 800')
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:of|ka)?\s*(\d+(?:\.\d+)?)", expr, flags=re.IGNORECASE)
        if pct_match:
            pct_val = float(pct_match.group(1))
            total_val = float(pct_match.group(2))
            res = (pct_val / 100.0) * total_val
            return ToolResult(
                success=True,
                output=f"{expr} = {res:g}",
                metadata={"result": res, "expression": expr}
            )

        # Sanitize clean arithmetic string
        clean_expr = expr.replace("x", "*").replace("X", "*").replace("^", "**").replace("÷", "/")
        # Remove words like 'calculate', 'what is', 'solve'
        clean_expr = re.sub(r"(?i)\b(calculate|what is|solve|math|ans|equal to|equals|\?)\b", "", clean_expr).strip()

        try:
            tree = ast.parse(clean_expr, mode='eval')
            result = safe_eval(tree)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return ToolResult(
                success=True,
                output=f"{clean_expr} = {result}",
                metadata={"result": result, "expression": clean_expr}
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Could not compute expression '{clean_expr}': {e}")
