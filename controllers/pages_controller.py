"""
AJAX AI - MVC Controller: Dedicated Multi-Page Web Application Router
Serves clean HTML pages with automatic authentication guard:
- Unauthenticated visitors are automatically redirected to /AJAX/login
- Authenticated users access: /AJAX/dashboard, /AJAX/chat, /memory, /system, /documents, /brain, /settings
- Strictly Admin-only: /AJAX/admin
"""

import os
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from controllers.auth_controller import get_current_user_from_request

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

def require_auth_page(request: Request) -> Optional[RedirectResponse]:
    """Guards protected pages: redirects unauthenticated requests to /AJAX/login."""
    user = get_current_user_from_request(request)
    if not user:
        target = request.url.path
        return RedirectResponse(url=f"/AJAX/login?redirect={target}", status_code=302)
    return None


# ------------------------------------------------------------------------------
# Routing Handlers
# ------------------------------------------------------------------------------

# Root Redirects
@pages_router.get("/AJAX", response_class=RedirectResponse)
@pages_router.get("/AJAX/", response_class=RedirectResponse)
@pages_router.get("/ajax", response_class=RedirectResponse)
@pages_router.get("/ajax/", response_class=RedirectResponse)
async def ajax_root(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse(url="/AJAX/login", status_code=302)
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)

# Unified Login & Register Page
@pages_router.get("/login", response_class=RedirectResponse)
@pages_router.get("/login/", response_class=RedirectResponse)
async def redirect_login():
    return RedirectResponse(url="/AJAX/login", status_code=302)

@pages_router.get("/AJAX/login", response_class=HTMLResponse)
@pages_router.get("/ajax/login", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    user = get_current_user_from_request(request)
    if user:
        # User is already signed in! Redirect to intended destination or dashboard
        redirect_target = request.query_params.get("redirect")
        if redirect_target and "/admin" in redirect_target and user.get("role") != "admin":
            redirect_target = "/AJAX/dashboard"
        elif not redirect_target or "/login" in redirect_target:
            redirect_target = "/AJAX/admin" if user.get("role") == "admin" else "/AJAX/dashboard"
        return RedirectResponse(url=redirect_target, status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="pages/login.html",
        context={"active_page": "login"}
    )

# Dedicated Administrator Panel (Strictly Admin Only)
@pages_router.get("/admin", response_class=RedirectResponse)
@pages_router.get("/admin/", response_class=RedirectResponse)
async def redirect_admin():
    return RedirectResponse(url="/AJAX/admin", status_code=302)

@pages_router.get("/AJAX/admin", response_class=HTMLResponse)
@pages_router.get("/ajax/admin", response_class=HTMLResponse)
async def serve_admin_page(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse(url="/AJAX/login?redirect=/AJAX/admin&reason=admin_required", status_code=302)
    if user.get("role") != "admin":
        return RedirectResponse(url="/AJAX/login?redirect=/AJAX/admin&reason=admin_required", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="pages/admin.html",
        context={"active_page": "admin", "current_user": user}
    )

# Main Dashboard (Protected)
@pages_router.get("/AJAX/dashboard", response_class=HTMLResponse)
async def serve_dashboard_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={"active_page": "dashboard"}
    )

# AI Chat Studio (Protected)
@pages_router.get("/AJAX/chat", response_class=HTMLResponse)
async def serve_chat_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/chat.html",
        context={"active_page": "chat"}
    )

# Retired Routes Redirects
@pages_router.get("/AJAX/tools", response_class=RedirectResponse)
@pages_router.get("/AJAX/tools/{tool_slug:path}", response_class=RedirectResponse)
@pages_router.get("/AJAX/apis", response_class=RedirectResponse)
@pages_router.get("/AJAX/apis/{api_slug:path}", response_class=RedirectResponse)
@pages_router.get("/AJAX/webcams", response_class=RedirectResponse)
async def redirect_retired_pages():
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)

# Core Subsystem: Memory (Protected)
@pages_router.get("/AJAX/memory", response_class=HTMLResponse)
async def serve_memory_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/memory.html",
        context={"active_page": "memory"}
    )

# Core Subsystem: System Diagnostics (Protected)
@pages_router.get("/AJAX/system", response_class=HTMLResponse)
async def serve_system_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/system.html",
        context={"active_page": "system"}
    )

# Core Subsystem: Documents & RAG (Protected)
@pages_router.get("/AJAX/documents", response_class=HTMLResponse)
async def serve_documents_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/documents.html",
        context={"active_page": "documents"}
    )

# Retired Pages & Subsystems Redirects
@pages_router.get("/AJAX/scheduler", response_class=RedirectResponse)
@pages_router.get("/AJAX/web-tools", response_class=RedirectResponse)
@pages_router.get("/AJAX/plugins", response_class=RedirectResponse)
@pages_router.get("/AJAX/schema", response_class=RedirectResponse)
@pages_router.get("/AJAX/workflows", response_class=RedirectResponse)
async def redirect_retired_scheduler_and_tools():
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)

# Core Subsystem: Brain & Neural Intent (Protected)
@pages_router.get("/AJAX/brain", response_class=HTMLResponse)
async def serve_brain_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/brain.html",
        context={"active_page": "brain"}
    )

# Core Subsystem: Settings (Protected)
@pages_router.get("/AJAX/settings", response_class=HTMLResponse)
async def serve_settings_page(request: Request):
    if auth_redirect := require_auth_page(request):
        return auth_redirect

    return templates.TemplateResponse(
        request=request,
        name="pages/settings.html",
        context={"active_page": "settings"}
    )
