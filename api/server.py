"""
AJAX AI - FastAPI Application & MVC Server
Coordinates Models, Views, and Controllers into a high-performance REST API & Web Dashboard.
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from controllers.chat_controller import chat_router
from controllers.upload_controller import upload_router
from controllers.system_controller import system_router
from controllers.tools_controller import tools_router
from controllers.memory_controller import memory_router
from core.logger import ajax_logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS_DIR = os.path.join(BASE_DIR, "views")
STATIC_DIR = os.path.join(VIEWS_DIR, "static")
TEMPLATES_DIR = os.path.join(VIEWS_DIR, "templates")

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

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Mount Static Assets (CSS & JS)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Register MVC Controller Routers
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(system_router)
app.include_router(tools_router)
app.include_router(memory_router)

# Main View Dashboard Route (Serves Decoupled Frontend or MVC Views)
@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_dashboard():
    # Prioritize standalone frontend if present
    frontend_index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(frontend_index):
        with open(frontend_index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)

    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>AJAX AI Server Online</h1>", status_code=200)

def start_server(host: str = "127.0.0.1", port: int = 8000):
    ajax_logger.info(f"Starting AJAX AI FastAPI MVC Server on http://{host}:{port}")
    print(f"\n==================================================================")
    print(f"  [*] AJAX AI FastAPI MVC Server Online: http://{host}:{port}")
    print(f"  [*] Interactive Swagger Docs:          http://{host}:{port}/docs")
    print(f"  [*] Interactive ReDoc:                 http://{host}:{port}/redoc")
    print(f"  [*] Web UI, Voice & Doc Upload Live! Press Ctrl+C to stop.")
    print(f"==================================================================\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
