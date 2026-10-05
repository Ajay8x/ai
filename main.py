"""
AJAX AI - Master Application Entry Point
Adaptive Intelligence & Autonomous eXecution
"""

import sys
import argparse
import webbrowser
from database.db import init_db
import tools # Auto-registers all system, app, web, scheduler, and memory tools
from core.diagnostics import diagnostics
from core.logger import ajax_logger
from ui.cli import cli
from voice.manager import voice_manager
from api.server import start_server
from config.config_loader import config

def main():
    parser = argparse.ArgumentParser(description="AJAX AI - Autonomous Personal Assistant")
    parser.add_argument("--voice", action="store_true", help="Start in Voice Assistant Mode")
    parser.add_argument("--server", action="store_true", help="Start Local REST API & Web Dashboard Server")
    parser.add_argument("--gui", action="store_true", help="Start Web UI and open in browser")
    parser.add_argument("--diagnostics", action="store_true", help="Run System Health Check and exit")
    parser.add_argument("--port", type=int, default=8000, help="Port for REST server / GUI")

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

    if args.voice:
        ajax_logger.info("Starting AJAX AI in Voice Mode...")
        voice_manager.run_loop()
    elif args.gui:
        ajax_logger.info(f"Starting AJAX AI GUI on port {args.port}...")
        webbrowser.open(f"http://127.0.0.1:{args.port}")
        start_server(port=args.port)
    elif args.server:
        ajax_logger.info(f"Starting AJAX AI Server on port {args.port}...")
        start_server(port=args.port)
    else:
        # Default: Interactive CLI with full natural language, tools, memory, and slash commands
        cli.run()

if __name__ == "__main__":
    main()