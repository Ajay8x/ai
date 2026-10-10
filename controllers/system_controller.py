"""
AJAX AI - MVC Controller: System Diagnostics, Health Checks & Logs
"""

import os
from fastapi import APIRouter
from system.monitor import system_monitor
from core.diagnostics import diagnostics
from core.logger import LOGS_DIR

system_router = APIRouter(prefix="/api", tags=["System & Diagnostics"])

@system_router.get("/status")
async def get_system_status():
    return system_monitor.get_full_diagnostics()

@system_router.get("/diagnostics")
async def get_system_diagnostics():
    return diagnostics.run_health_check()

@system_router.get("/logs")
async def get_recent_logs():
    log_file = os.path.join(LOGS_DIR, "ajax.log")
    lines = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f.readlines()[-30:] if line.strip()]
        except Exception:
            pass
    return {"logs": lines}
