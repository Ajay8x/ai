"""
AJAX AI - FastAPI Application & MVC Server
Coordinates Models, Views, and Controllers into a high-performance REST API & Web Dashboard.
"""

import sys
import os
import uuid
import time
import threading
from collections import defaultdict, deque
from contextlib import asynccontextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from controllers.chat_controller import chat_router
from controllers.upload_controller import upload_router
from controllers.system_controller import system_router
from controllers.tools_controller import tools_router
from controllers.memory_controller import memory_router
from controllers.pages_controller import pages_router
from controllers.auth_controller import auth_router
from controllers.auth_controller import require_admin
from database.db import get_db_connection, init_db, is_mongo_active
from config.config_loader import config
from core.logger import ajax_logger

VIEWS_DIR = os.path.join(BASE_DIR, "views")
STATIC_DIR = os.path.join(VIEWS_DIR, "static")
TEMPLATES_DIR = os.path.join(VIEWS_DIR, "templates")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

_RATE_LIMITS = {
    "/api/auth/login": (10, 60),
    "/api/auth/register": (5, 300),
    "/api/auth/demo-login": (10, 60),
    "/api/chat": (30, 60),
    "/api/chat/stream": (30, 60),
    "/api/upload": (10, 60),
    "/api/tools/execute": (60, 60),
    "/api/neural/predict": (60, 60),
}
_RATE_BUCKETS = defaultdict(deque)
_RATE_LIMIT_LOCK = threading.Lock()


def _rate_limit_exceeded(request: Request) -> tuple[bool, int]:
    """Apply a bounded per-process limiter to expensive state-changing APIs."""
    policy = _RATE_LIMITS.get(request.url.path)
    if not policy or request.method != "POST":
        return False, 0

    limit, window_seconds = policy
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"
    now = time.time()
    with _RATE_LIMIT_LOCK:
        bucket = _RATE_BUCKETS[key]
        while bucket and now - bucket[0] >= window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(window_seconds - (now - bucket[0])))
            return True, retry_after
        bucket.append(now)
        return False, 0


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_db()
    except Exception as e:
        ajax_logger.error(f"Startup database initialization error: {e}")
        if os.environ.get("VERCEL"):
            raise
    yield


app = FastAPI(
    title="AJAX AI - Autonomous Assistant API ⚡",
    description="Production-Grade FastAPI MVC Backend for AJAX AI",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs" if config.api_docs_enabled else None,
    redoc_url="/redoc" if config.api_docs_enabled else None,
    openapi_url="/openapi.json" if config.api_docs_enabled else None,
)

# CORS Middleware. Same-origin browser requests do not need CORS; only explicitly
# configured trusted origins are allowed to send credentialed requests.
_cors_origins = [origin.strip() for origin in config.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
)


@app.middleware("http")
async def request_security_middleware(request: Request, call_next):
    """Add correlation IDs, basic browser CSRF protection, and safe headers."""
    request_id = request.headers.get("X-Request-ID", "").strip()[:128] or uuid.uuid4().hex

    limited, retry_after = _rate_limit_exceeded(request)
    if limited:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
            headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
        )

    # Cookie-authenticated state changes must originate from this site (or an
    # explicitly configured trusted CORS origin). Bearer clients do not need
    # this browser-specific check.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.cookies.get("ajax_session_token"):
        origin = request.headers.get("origin", "").rstrip("/")
        if origin:
            forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip()
            forwarded_host = request.headers.get("x-forwarded-host", "").split(",", 1)[0].strip()
            expected_scheme = forwarded_proto or request.url.scheme
            expected_host = forwarded_host or request.headers.get("host", "")
            expected_origin = f"{expected_scheme}://{expected_host}".rstrip("/")
            trusted_origins = {value.rstrip("/") for value in _cors_origins}
            if origin != expected_origin and origin not in trusted_origins:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Cross-site request blocked."},
                    headers={"X-Request-ID": request_id},
                )

    try:
        response = await call_next(request)
    except Exception:
        ajax_logger.exception("Unhandled request failure", extra={"request_id": request_id})
        response = JSONResponse(status_code=500, content={"detail": "Internal server error."})

    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response

# Mount Static Assets
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

css_dir = os.path.join(FRONTEND_DIR, "css") if os.path.exists(os.path.join(FRONTEND_DIR, "css")) else os.path.join(STATIC_DIR, "css")
if os.path.exists(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="frontend_css")
    app.mount("/AJAX/css", StaticFiles(directory=css_dir), name="ajax_css")
    app.mount("/ajax/css", StaticFiles(directory=css_dir), name="ajax_lower_css")

js_dir = os.path.join(FRONTEND_DIR, "js") if os.path.exists(os.path.join(FRONTEND_DIR, "js")) else os.path.join(STATIC_DIR, "js")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="frontend_js")
    app.mount("/AJAX/js", StaticFiles(directory=js_dir), name="ajax_js")
    app.mount("/ajax/js", StaticFiles(directory=js_dir), name="ajax_lower_js")

# Register MVC Controller Routers
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(system_controller_router := system_router)
app.include_router(tools_router)
app.include_router(memory_router)

# Health Check Endpoint
@app.get("/api/health")
async def health_check():
    configured_database = config.database.db_type.lower()
    active_database = configured_database
    database_ready = False
    if configured_database == "mongodb":
        database_ready = is_mongo_active()
        if not database_ready and config.allow_sqlite_fallback:
            try:
                conn = get_db_connection()
                active_database = "postgres" if conn.is_postgres else "sqlite"
                conn.close()
                database_ready = True
            except Exception:
                database_ready = False
    else:
        try:
            conn = get_db_connection()
            active_database = "postgres" if conn.is_postgres else "sqlite"
            conn.close()
            database_ready = True
        except Exception:
            database_ready = False
    status = "healthy" if database_ready else "unhealthy"
    return JSONResponse({
        "status": status,
        "service": "AJAX AI",
        "version": "3.0.0",
        "serverless": bool(os.environ.get("VERCEL")),
        "database": active_database,
        "configured_database": configured_database,
        "database_ready": database_ready
    }, status_code=200 if database_ready else 503)

# Serverless Diagnosis Endpoint
@app.get("/api/debug")
async def debug_endpoint(admin: dict = Depends(require_admin)):
    if not config.debug:
        raise HTTPException(status_code=404, detail="Not found")
    import traceback
    info = {
        "cwd": os.getcwd(),
        "base_dir": BASE_DIR,
        "views_dir": VIEWS_DIR,
        "views_exists": os.path.exists(VIEWS_DIR),
        "templates_dir": TEMPLATES_DIR,
        "templates_exists": os.path.exists(TEMPLATES_DIR),
        "cwd_listdir": os.listdir(os.getcwd()) if os.path.exists(os.getcwd()) else [],
        "base_listdir": os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else [],
    }
    if os.path.exists(VIEWS_DIR):
        info["views_listdir"] = os.listdir(VIEWS_DIR)
        t_dir = os.path.join(VIEWS_DIR, "templates")
        if os.path.exists(t_dir):
            info["templates_listdir"] = os.listdir(t_dir)
            p_dir = os.path.join(t_dir, "pages")
            if os.path.exists(p_dir):
                info["pages_listdir"] = os.listdir(p_dir)
    
    try:
        from controllers.pages_controller import templates
        template = templates.get_template("pages/dashboard.html")
        info["template_loaded"] = True
    except Exception as e:
        info["template_error"] = traceback.format_exc()

    return JSONResponse(info)

# Redirect root to /AJAX/dashboard (or /AJAX/login if unauthenticated)
@app.get("/")
async def root_redirect(request: Request):
    from controllers.auth_controller import get_current_user_from_request
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse(url="/AJAX/login", status_code=302)
    return RedirectResponse(url="/AJAX/dashboard", status_code=302)


def start_server(host: str = None, port: int = 8000):
    host = host or config.host
    ajax_logger.info(f"Starting AJAX AI FastAPI MVC Server on http://{host}:{port}/AJAX")
    print(f"\n==================================================================")
    print(f"  [*] AJAX AI Web Dashboard:             http://{host}:{port}/AJAX")
    if config.api_docs_enabled:
        print(f"  [*] Interactive Swagger Docs:          http://{host}:{port}/docs")
        print(f"  [*] Interactive ReDoc:                 http://{host}:{port}/redoc")
    print(f"  [*] Web UI, Voice & Doc Upload Live! Press Ctrl+C to stop.")
    print(f"==================================================================\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")

