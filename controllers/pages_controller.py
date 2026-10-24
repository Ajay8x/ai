"""
AJAX AI - MVC Controller: Dedicated Multi-Page Web Application Router
Serves clean HTML pages for:
- /AJAX/dashboard (Main command center)
- /AJAX/chat (Dedicated AI Chat Studio)
- Dedicated core pages: /memory, /system, /documents, /brain, /settings
All retired and legacy routes safely redirect to /AJAX/dashboard.
"""

import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

candidate_template_dirs = [
    os.path.join(BASE_DIR, "views", "templates"),
    os.path.join(os.getcwd(), "views", "templates"),
    os.path.join("/var", "task", "views", "templates"),
]
valid_template_dirs = [d for d in candidate_template_dirs if os.path.exists(d)]
TEMPLATES_DIR = valid_template_dirs if valid_template_dirs else os.path.join(BASE_DIR, "views", "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
pages_router = APIRouter(tags=["Multi-Page Dashboard"])

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
    try:
        return templates.TemplateResponse("pages/dashboard.html", {
            "request": request,
            "active_page": "dashboard"
        })
    except Exception as e:
        import traceback
        return HTMLResponse(
            f"<h3>Dashboard Render Error</h3><pre>{traceback.format_exc()}</pre>",
            status_code=500
        )

# AI Chat Studio
@pages_router.get("/AJAX/chat", response_class=HTMLResponse)
async def serve_chat_page(request: Request):
    return templates.TemplateResponse("pages/chat.html", {
        "request": request,
        "active_page": "chat"
    })

# Retired Routes Redirects
@pages_router.get("/AJAX/tools", response_class=RedirectResponse)
@pages_router.get("/AJAX/tools/{tool_slug:path}", response_class=RedirectResponse)
@pages_router.get("/AJAX/apis", response_class=RedirectResponse)
@pages_router.get("/AJAX/apis/{api_slug:path}", response_class=RedirectResponse)
@pages_router.get("/AJAX/webcams", response_class=RedirectResponse)
async def redirect_retired_pages():
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)

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

# Retired Pages & Subsystems Redirects
@pages_router.get("/AJAX/scheduler", response_class=RedirectResponse)
@pages_router.get("/AJAX/web-tools", response_class=RedirectResponse)
@pages_router.get("/AJAX/plugins", response_class=RedirectResponse)
@pages_router.get("/AJAX/schema", response_class=RedirectResponse)
@pages_router.get("/AJAX/workflows", response_class=RedirectResponse)
async def redirect_retired_scheduler_and_tools():
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
