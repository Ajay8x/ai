"""
Vercel Serverless Entry Point for AJAX AI
Exposes the FastAPI application instance for Vercel Python Runtime.
"""

from api.server import app

# Vercel looks for 'app' as ASGI handler
__all__ = ["app"]
