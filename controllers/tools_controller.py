"""
AJAX AI - MVC Controller: Tool Execution & Registry Management
"""

from fastapi import APIRouter
from models.schemas import ToolExecRequest
from tools.registry import registry

tools_router = APIRouter(prefix="/api", tags=["Tools & Automation"])

@tools_router.get("/tools")
async def list_registered_tools():
    tools_data = [{"name": t.name, "description": t.description, "permission": t.permission} for t in registry.list_tools()]
    return {"tools": tools_data}

@tools_router.post("/tools/execute")
async def execute_tool_action(req: ToolExecRequest):
    res = registry.execute_tool(req.tool_name, parameters=req.parameters or {}, confirmed_by_user=req.confirmed or False)
    return res.to_dict()
