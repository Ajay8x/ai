"""
Vercel Serverless Entry Point for AJAX AI
Exposes the FastAPI application instance for Vercel Python Runtime.
"""

import sys
import os

# Ensure the project root directory is on the Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("VERCEL", "1")

from api.server import app

# Vercel looks for 'app' as ASGI handler
__all__ = ["app"]
