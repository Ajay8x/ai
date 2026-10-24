"""
AJAX AI - FastAPI Application & MVC Server
Coordinates Models, Views, and Controllers into a high-performance REST API & Web Dashboard.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
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
from database.db import init_db
from core.logger import ajax_logger

VIEWS_DIR = os.path.join(BASE_DIR, "views")
STATIC_DIR = os.path.join(VIEWS_DIR, "static")
TEMPLATES_DIR = os.path.join(VIEWS_DIR, "templates")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(
    title="AJAX AI - Autonomous Assistant API ⚡",
    description="Production-Grade FastAPI MVC Backend for AJAX AI",
    version="3.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(system_controller_router := system_router)
app.include_router(tools_router)
app.include_router(memory_router)

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
    except Exception as e:
        ajax_logger.error(f"Startup database initialization error: {e}")

# Health Check Endpoint
@app.get("/api/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "service": "AJAX AI",
        "version": "3.0.0",
        "serverless": bool(os.environ.get("VERCEL"))
    })

# Serverless Diagnosis Endpoint
@app.get("/api/debug")
async def debug_endpoint():
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

# Redirect root to /AJAX/dashboard
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/AJAX/dashboard")


def start_server(host: str = "127.0.0.1", port: int = 8000):
    ajax_logger.info(f"Starting AJAX AI FastAPI MVC Server on http://{host}:{port}/AJAX")
    print(f"\n==================================================================")
    print(f"  [*] AJAX AI Web Dashboard:             http://{host}:{port}/AJAX")
    print(f"  [*] Interactive Swagger Docs:          http://{host}:{port}/docs")
    print(f"  [*] Interactive ReDoc:                 http://{host}:{port}/redoc")
    print(f"  [*] Web UI, Voice & Doc Upload Live! Press Ctrl+C to stop.")
    print(f"==================================================================\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")

