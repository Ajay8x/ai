"""
AJAX AI - Authentication & Role-Based Access Control Controller
Unified authentication engine providing:
- One-Tab User Login & Account Registration
- Dedicated Administrator Authentication Portal
- Protected Admin Management APIs (User administration, KPI stats, system actions)
- Secure session tokens via Cookies & Bearer Headers
"""

import secrets
import time
import os
import threading
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database.crud import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    list_all_users,
    verify_password,
    update_user_status,
    update_user_role,
    delete_user,
    update_user_last_login,
    list_conversations,
    search_memories,
    is_mongo_active,
    save_auth_session,
    get_auth_session,
    delete_auth_session,
    purge_expired_auth_sessions
)
from core.logger import ajax_logger
from config.config_loader import config

auth_router = APIRouter(prefix="/api", tags=["Authentication & Administration"])

# In-Memory Session Token Cache: token -> {user_id, role, username, expires_at}
_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SECONDS = 30 * 24 * 3600  # 30 Days Persistent Session
_LOGIN_FAILURES = defaultdict(deque)
_LOGIN_RATE_LOCK = threading.Lock()
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5
_LAST_SESSION_CLEANUP = 0.0
_SESSION_CLEANUP_LOCK = threading.Lock()
SESSION_CLEANUP_INTERVAL_SECONDS = 60


def evict_expired_sessions() -> int:
    """Remove expired in-memory and persistent sessions on a bounded cadence."""
    global _LAST_SESSION_CLEANUP
    now = time.time()
    if now - _LAST_SESSION_CLEANUP < SESSION_CLEANUP_INTERVAL_SECONDS:
        return 0
    with _SESSION_CLEANUP_LOCK:
        if now - _LAST_SESSION_CLEANUP < SESSION_CLEANUP_INTERVAL_SECONDS:
            return 0
        _LAST_SESSION_CLEANUP = now
        expired = [token for token, session in list(_SESSIONS.items()) if session.get("expires_at", 0) <= now]
        for token in expired:
            _SESSIONS.pop(token, None)
        try:
            purge_expired_auth_sessions()
        except Exception as e:
            ajax_logger.warning(f"Expired session cleanup notice: {e}")
        return len(expired)


def _login_key(request: Request, username: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{username}"


def _login_is_limited(key: str) -> bool:
    now = time.time()
    with _LOGIN_RATE_LOCK:
        attempts = _LOGIN_FAILURES[key]
        while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
            attempts.popleft()
        return len(attempts) >= LOGIN_MAX_FAILURES


def _record_login_failure(key: str):
    with _LOGIN_RATE_LOCK:
        _LOGIN_FAILURES[key].append(time.time())


def _clear_login_failures(key: str):
    with _LOGIN_RATE_LOCK:
        _LOGIN_FAILURES.pop(key, None)


def _set_session_cookie(response: Response, token: str):
    secure_cookie = os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true" or bool(os.getenv("VERCEL"))
    response.set_cookie(
        key="ajax_session_token",
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/"
    )

def create_session(user: Dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + SESSION_TTL_SECONDS
    sess_data = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user.get("role", "user"),
        "full_name": user.get("full_name", user["username"]),
        "expires_at": expires_at
    }
    # Cache in fast RAM
    _SESSIONS[token] = sess_data
    # Persist to database so session survives server restarts & reloads
    try:
        save_auth_session(token, user, expires_at)
    except Exception as e:
        ajax_logger.warning(f"Could not persist session to DB: {e}")

    return token

def get_current_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """Resolves authenticated user from Cookie or Authorization header with DB fallback."""
    evict_expired_sessions()
    token = request.cookies.get("ajax_session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()

    if not token:
        return None

    # 1. Fast RAM check
    sess = _SESSIONS.get(token)

    # 2. If not in RAM (e.g. after server restart or multi-process), check DB
    if not sess:
        try:
            db_sess = get_auth_session(token)
            if db_sess:
                sess = {
                    "user_id": db_sess["user_id"],
                    "username": db_sess["username"],
                    "role": db_sess.get("role", "user"),
                    "full_name": db_sess.get("full_name", db_sess["username"]),
                    "expires_at": db_sess["expires_at"]
                }
                # Re-populate RAM cache
                _SESSIONS[token] = sess
        except Exception as e:
            ajax_logger.warning(f"Session DB lookup error: {e}")

    if not sess:
        return None

    if time.time() > sess["expires_at"]:
        _SESSIONS.pop(token, None)
        try:
            delete_auth_session(token)
        except Exception:
            pass
        return None

    # Fetch fresh user details
    user = get_user_by_id(sess["user_id"])
    if not user or user.get("status") == "blocked":
        _SESSIONS.pop(token, None)
        try:
            delete_auth_session(token)
        except Exception:
            pass
        return None

    return user

def require_authenticated_user(request: Request) -> Dict[str, Any]:
    """Dependency that requires a valid login session for protected APIs."""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")
    return user

def require_admin(request: Request) -> Dict[str, Any]:
    """Dependency for strictly protecting admin endpoints."""
    user = require_authenticated_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Administrator privileges required.")
    return user


# ------------------------------------------------------------------------------
# Request Schemas
# ------------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2)
    # Login validates presence only; registration owns the password-strength policy.
    password: str = Field(..., min_length=1, max_length=256)
    mode: str = Field("user", description="'user' or 'admin'")

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=12)
    full_name: str = Field(..., min_length=2)
    email: Optional[str] = None

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(active|blocked)$")

class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|user)$")


# ------------------------------------------------------------------------------
# Authentication Endpoints
# ------------------------------------------------------------------------------
@auth_router.post("/auth/login")
async def login_user(request: Request, payload: LoginRequest, response: Response):
    """Unified Login endpoint for both Regular Users and Administrators."""
    username = payload.username.strip().lower()
    rate_key = _login_key(request, username)
    if _login_is_limited(rate_key):
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(LOGIN_WINDOW_SECONDS)},
            content={"success": False, "message": "Too many failed login attempts. Try again later."}
        )
    user = get_user_by_username(username)

    if not user:
        _record_login_failure(rate_key)
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid username or password."}
        )

    if not verify_password(payload.password, user.get("password_hash", "")):
        _record_login_failure(rate_key)
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid username or password."}
        )

    if user.get("status") == "blocked":
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Account has been suspended by an administrator."}
        )

    _clear_login_failures(rate_key)
    # Issue session
    token = create_session(user)
    update_user_last_login(user["id"])

    response = JSONResponse({
        "success": True,
        "message": f"Welcome back, {user.get('full_name', username)}!",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"]
        }
    })

    _set_session_cookie(response, token)
    return response


@auth_router.post("/auth/demo-login")
async def demo_quick_login(response: Response):
    """Instant demo login when explicitly enabled and configured."""
    from database.crud import seed_default_demo_user

    if not config.demo_login_enabled:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Demo login is disabled."}
        )

    seed_default_demo_user()

    demo_username = config.demo_username.strip().lower()
    user = get_user_by_username(demo_username)
    if not user:
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "Demo login is enabled but not configured correctly."}
        )

    token = create_session(user)
    update_user_last_login(user["id"])

    res = JSONResponse({
        "success": True,
        "message": "Welcome to AJAX AI Demo Account!",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user.get("full_name", "Demo User"),
            "email": user.get("email", "demo@ajax.ai"),
            "role": user.get("role", "user"),
            "status": user.get("status", "active")
        }
    })

    _set_session_cookie(res, token)
    return res


@auth_router.post("/auth/register")
async def register_user(payload: RegisterRequest, response: Response):
    """Allows any new user to create an account and immediately sign in."""
    username = payload.username.strip().lower()
    
    # Check if username already taken
    existing = get_user_by_username(username)
    if existing:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Username '{username}' is already taken. Please choose another."}
        )

    created = create_user(
        username=username,
        password=payload.password,
        full_name=payload.full_name,
        email=payload.email or f"{username}@ajax.ai",
        role="user"
    )

    if not created:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to create user account. Please try again."}
        )

    token = create_session(created)
    ajax_logger.info(f"New user registered: '{username}' ({created['id']})")

    response = JSONResponse({
        "success": True,
        "message": f"Account created successfully! Welcome, {created['full_name']}.",
        "user": created
    })

    _set_session_cookie(response, token)
    return response


@auth_router.get("/auth/me")
async def get_current_user_profile(request: Request):
    """Returns currently authenticated user profile or unauthenticated status."""
    user = get_current_user_from_request(request)
    if not user:
        return JSONResponse({"authenticated": False, "user": None})

    return JSONResponse({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user.get("full_name", user["username"]),
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "status": user.get("status", "active"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }
    })


@auth_router.post("/auth/logout")
async def logout_user(request: Request, response: Response):
    """Logs out user and invalidates session token."""
    token = request.cookies.get("ajax_session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()

    if token:
        _SESSIONS.pop(token, None)
        try:
            delete_auth_session(token)
        except Exception:
            pass

    resp = JSONResponse({"success": True, "message": "Signed out successfully."})
    resp.delete_cookie(key="ajax_session_token", path="/")
    return resp


# ------------------------------------------------------------------------------
# Protected Admin Panel Endpoints (Strictly require_admin)
# ------------------------------------------------------------------------------
@auth_router.get("/admin/users")
async def admin_get_all_users(admin: Dict[str, Any] = Depends(require_admin)):
    """Admin Only: Lists all registered users with their roles and status."""
    users = list_all_users()
    return JSONResponse({
        "success": True,
        "count": len(users),
        "users": users
    })


@auth_router.post("/admin/users/{user_id}/status")
async def admin_update_user_status(
    user_id: str,
    payload: StatusUpdateRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Admin Only: Toggles user between active and blocked."""
    if user_id == admin["id"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "You cannot block your own administrative account."}
        )

    updated = update_user_status(user_id, payload.status)
    if not updated:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

    action = "suspended" if payload.status == "blocked" else "activated"
    ajax_logger.info(f"Admin '{admin['username']}' {action} user '{user_id}'")
    return JSONResponse({"success": True, "message": f"User account has been {action}."})


@auth_router.post("/admin/users/{user_id}/role")
async def admin_update_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Admin Only: Promotes or demotes user role between admin and user."""
    if user_id == admin["id"] and payload.role != "admin":
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "You cannot revoke your own administrator role."}
        )

    updated = update_user_role(user_id, payload.role)
    if not updated:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

    ajax_logger.info(f"Admin '{admin['username']}' set user '{user_id}' role to '{payload.role}'")
    return JSONResponse({"success": True, "message": f"User role updated to '{payload.role}'."})


@auth_router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Admin Only: Permanently deletes a user account."""
    if user_id == admin["id"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "You cannot delete your own administrative account."}
        )

    deleted = delete_user(user_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})

    ajax_logger.info(f"Admin '{admin['username']}' deleted user '{user_id}'")
    return JSONResponse({"success": True, "message": "User account permanently deleted."})


@auth_router.get("/admin/stats")
async def admin_get_system_stats(admin: Dict[str, Any] = Depends(require_admin)):
    """Admin Only: Returns high-level KPI and diagnostic metrics."""
    users = list_all_users()
    admins_count = sum(1 for u in users if u.get("role") == "admin")
    active_count = sum(1 for u in users if u.get("status") == "active")

    convs = list_conversations(limit=200, include_all=True)
    memories = search_memories(limit=200, include_all=True)

    from ai.neural.intent_classifier import intent_classifier
    num_intents = len(intent_classifier.classes) if hasattr(intent_classifier, "classes") else 20
    vocab_size = len(intent_classifier.vocab) if hasattr(intent_classifier, "vocab") else 0

    return JSONResponse({
        "success": True,
        "users": {
            "total": len(users),
            "admins": admins_count,
            "regular": len(users) - admins_count,
            "active": active_count,
            "blocked": len(users) - active_count
        },
        "system": {
            "conversations_count": len(convs),
            "memories_count": len(memories),
            "database_type": "MongoDB Atlas (Cloud)" if is_mongo_active() else "SQLite (Local)",
            "neural_intents_count": num_intents,
            "neural_vocab_size": vocab_size,
            "active_sessions": len(_SESSIONS)
        }
    })
