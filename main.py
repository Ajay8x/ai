"""
AJAX AI - Master Application Entry Point
FastAPI MVC Backend & Standalone Frontend Server
"""

import sys
import argparse
import webbrowser
from database.db import init_db
import tools # Auto-registers all system, app, web, scheduler, and memory tools
from core.diagnostics import diagnostics
from core.logger import ajax_logger
from api.server import start_server
from config.config_loader import config

def main():
    parser = argparse.ArgumentParser(description="AJAX AI - Autonomous Assistant Backend & Web App")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI server (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser on startup")
    parser.add_argument("--diagnostics", action="store_true", help="Run System Health Check and exit")

    args = parser.parse_args()

    # Step 1: Initialize Database & Core subsystems
    init_db()

    if args.diagnostics:
        report = diagnostics.run_health_check()
        print("\n=== AJAX AI DIAGNOSTIC REPORT ===")
        print(f"Overall Status: {report['overall_status']}")
        for k, v in report['subsystems'].items():
            print(f" • {k.upper()}: {v}")
        return

    # Default: Start FastAPI MVC & Web Application Server
    ajax_logger.info(f"Starting AJAX AI FastAPI MVC Server on port {args.port}...")
    if not args.no_browser:
        try:
            webbrowser.open(f"http://127.0.0.1:{args.port}/frontend/")
        except Exception:
            pass

    start_server(port=args.port)

if __name__ == "__main__":
    main()