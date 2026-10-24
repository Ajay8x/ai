"""
AJAX AI - MVC Controller: Dedicated Multi-Page Web Application Router
Serves clean HTML pages for:
- /AJAX/dashboard (Main command center)
- /AJAX/chat (Dedicated AI Chat Studio)
- /AJAX/tools (25 Tools Catalog) & /AJAX/tools/{tool_slug} (25 Individual Tool Pages)
- /AJAX/apis (16 APIs Catalog) & /AJAX/apis/{api_slug} (16 Individual API Pages)
- Dedicated core pages: /memory, /system, /documents, /scheduler, /web-tools, /plugins, /schema, /workflows, /brain, /settings
"""

import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import tools
import plugins
from tools.registry import registry
from core.permissions import PermissionLevel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "views", "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
pages_router = APIRouter(tags=["Multi-Page Dashboard"])

# ------------------------------------------------------------------------------
# Tool Presets Dictionary
# ------------------------------------------------------------------------------
TOOL_PRESETS: Dict[str, List[Dict[str, Any]]] = {
    "get_weather": [
        {"label": "New Delhi", "params": {"city": "New Delhi"}},
        {"label": "London", "params": {"city": "London"}},
        {"label": "Tokyo", "params": {"city": "Tokyo"}},
    ],
    "get_weather_forecast": [
        {"label": "Delhi (3 Days)", "params": {"city": "New Delhi", "days": 3}},
        {"label": "Mumbai (5 Days)", "params": {"city": "Mumbai", "days": 5}},
    ],
    "calculate": [
        {"label": "25 * 4", "params": {"expression": "25 * 4"}},
        {"label": "15% of 800", "params": {"expression": "15% of 800"}},
        {"label": "sqrt(144) + 2^8", "params": {"expression": "sqrt(144) + 2^8"}},
    ],
    "scientific_calculate": [
        {"label": "sin(pi / 2)", "params": {"formula": "sin(pi / 2)"}},
        {"label": "log10(1000) * 5", "params": {"formula": "log10(1000) * 5"}},
    ],
    "search_files": [
        {"label": "Search Python Files", "params": {"query": "main.py"}},
        {"label": "Search Configs", "params": {"query": ".yaml"}},
    ],
    "read_file": [
        {"label": "Read Config", "params": {"file_path": "config/config.yaml"}},
    ],
    "delete_file": [
        {"label": "Test Temp File", "params": {"file_path": "scratch/temp_delete_test.txt"}},
    ],
    "remember_fact": [
        {"label": "Favorite IDE", "params": {"key": "favorite_ide", "value": "Antigravity IDE"}},
    ],
    "recall_memory": [
        {"label": "Recall IDE", "params": {"query": "favorite ide"}},
    ],
    "set_timer": [
        {"label": "30 Seconds", "params": {"duration": "30s", "label": "Quick Timer"}},
        {"label": "5 Minutes", "params": {"duration": "5m", "label": "Tea Break"}},
    ],
    "search_web": [
        {"label": "Python 3.12 Features", "params": {"query": "Python 3.12 new features"}},
    ],
    "search_wikipedia": [
        {"label": "James Webb Telescope", "params": {"query": "James Webb Space Telescope"}},
    ],
    "play_youtube": [
        {"label": "Lo-Fi Coding Beats", "params": {"query": "Lo-Fi coding beats"}},
    ],
    "open_website": [
        {"label": "FastAPI Docs", "params": {"url": "https://fastapi.tiangolo.com"}},
    ],
    "query_documents": [
        {"label": "Architecture Overview", "params": {"query": "system architecture"}},
    ],
    "save_quick_note": [
        {"label": "Quick Note", "params": {"title": "Dev Plan", "content": "Complete AJAX AI multi-page dashboard"}},
    ]
}

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------
def _get_tools_data() -> List[Dict[str, Any]]:
    tools = []
    for t in registry.list_tools():
        perm_str = t.permission.value if hasattr(t.permission, "value") else str(t.permission)
        cat_str = t.category.value if hasattr(t.category, "value") else str(t.category)
        slug = t.name.replace("_", "-")
        tools.append({
            "name": t.name,
            "slug": slug,
            "description": t.description,
            "category": cat_str,
            "permission": perm_str,
            "parameters_schema": getattr(t, "parameters_schema", {}) or {},
            "examples": TOOL_PRESETS.get(t.name, [])
        })
    return sorted(tools, key=lambda x: x["name"])

# ------------------------------------------------------------------------------
# Routing Handlers
# ------------------------------------------------------------------------------

# Root Redirects
@pages_router.get("/AJAX", response_class=RedirectResponse)
@pages_router.get("/AJAX/", response_class=RedirectResponse)
@pages_router.get("/ajax", response_class=RedirectResponse)
@pages_router.get("/ajax/", response_class=RedirectResponse)
async def ajax_root():
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)

# Main Dashboard
@pages_router.get("/AJAX/dashboard", response_class=HTMLResponse)
async def serve_dashboard_page(request: Request):
    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "active_page": "dashboard"
    })

# AI Chat Studio
@pages_router.get("/AJAX/chat", response_class=HTMLResponse)
async def serve_chat_page(request: Request):
    return templates.TemplateResponse("pages/chat.html", {
        "request": request,
        "active_page": "chat"
    })

# 25 Tools Overview
@pages_router.get("/AJAX/tools", response_class=HTMLResponse)
async def serve_tools_catalog_page(request: Request):
    tools = _get_tools_data()
    return templates.TemplateResponse("pages/tools_catalog.html", {
        "request": request,
        "active_page": "tools",
        "tools": tools
    })

# Individual Tool Pages (/AJAX/tools/{tool_slug})
@pages_router.get("/AJAX/tools/{tool_slug}", response_class=HTMLResponse)
async def serve_tool_detail_page(request: Request, tool_slug: str):
    tool_name = tool_slug.replace("-", "_")
    tool_obj = registry.get_tool(tool_name)
    if not tool_obj:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

    perm_str = tool_obj.permission.value if hasattr(tool_obj.permission, "value") else str(tool_obj.permission)
    cat_str = tool_obj.category.value if hasattr(tool_obj.category, "value") else str(tool_obj.category)
    tool_data = {
        "name": tool_obj.name,
        "slug": tool_slug,
        "description": tool_obj.description,
        "category": cat_str,
        "permission": perm_str,
        "parameters_schema": getattr(tool_obj, "parameters_schema", {}) or {},
        "examples": TOOL_PRESETS.get(tool_obj.name, [])
    }

    return templates.TemplateResponse("pages/tool_detail.html", {
        "request": request,
        "active_page": "tools",
        "tool": tool_data
    })

# Retired Public APIs Redirects
@pages_router.get("/AJAX/apis", response_class=RedirectResponse)
@pages_router.get("/AJAX/apis/{api_slug:path}", response_class=RedirectResponse)
@pages_router.get("/AJAX/webcams", response_class=RedirectResponse)
async def redirect_retired_apis():
    return RedirectResponse(url="/AJAX/tools", status_code=302)

# Core Subsystem: Memory
@pages_router.get("/AJAX/memory", response_class=HTMLResponse)
async def serve_memory_page(request: Request):
    return templates.TemplateResponse("pages/memory.html", {
        "request": request,
        "active_page": "memory"
    })

# Core Subsystem: System Diagnostics
@pages_router.get("/AJAX/system", response_class=HTMLResponse)
async def serve_system_page(request: Request):
    return templates.TemplateResponse("pages/system.html", {
        "request": request,
        "active_page": "system"
    })

# Core Subsystem: Documents & RAG
@pages_router.get("/AJAX/documents", response_class=HTMLResponse)
async def serve_documents_page(request: Request):
    return templates.TemplateResponse("pages/documents.html", {
        "request": request,
        "active_page": "documents"
    })

# Core Subsystem: Scheduler
@pages_router.get("/AJAX/scheduler", response_class=HTMLResponse)
async def serve_scheduler_page(request: Request):
    return templates.TemplateResponse("pages/scheduler.html", {
        "request": request,
        "active_page": "scheduler"
    })

# Core Subsystem: Web Tools
@pages_router.get("/AJAX/web-tools", response_class=HTMLResponse)
async def serve_web_tools_page(request: Request):
    return templates.TemplateResponse("pages/web_tools.html", {
        "request": request,
        "active_page": "web_tools"
    })

# Core Subsystem: Custom Plugins
@pages_router.get("/AJAX/plugins", response_class=HTMLResponse)
async def serve_plugins_page(request: Request):
    return templates.TemplateResponse("pages/plugins.html", {
        "request": request,
        "active_page": "plugins"
    })

# Retired Subsystems Redirects
@pages_router.get("/AJAX/schema", response_class=RedirectResponse)
@pages_router.get("/AJAX/workflows", response_class=RedirectResponse)
async def redirect_retired_schema_workflows():
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)

# Core Subsystem: Brain & Neural Intent
@pages_router.get("/AJAX/brain", response_class=HTMLResponse)
async def serve_brain_page(request: Request):
    return templates.TemplateResponse("pages/brain.html", {
        "request": request,
        "active_page": "brain"
    })

# Core Subsystem: Settings
@pages_router.get("/AJAX/settings", response_class=HTMLResponse)
async def serve_settings_page(request: Request):
    return templates.TemplateResponse("pages/settings.html", {
        "request": request,
        "active_page": "settings"
    })
