"""
AJAX AI - Database CRUD Operations
High-performance query abstractions for conversations, memories, tools, and tasks.
Seamlessly unifies MongoDB Atlas (Cloud) with PostgreSQL and SQLite (Local fallback).
"""

import uuid
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from database.db import get_db_connection, get_mongo_db, is_mongo_active, DB_LOCK
from core.logger import ajax_logger, error_logger

# ----------------- CONVERSATIONS & MESSAGES ----------------- #

def create_conversation(title: str = "New Conversation") -> str:
    conv_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.conversations.insert_one({
                "id": conv_id,
                "title": title,
                "created_at": now_str,
                "updated_at": now_str,
                "is_archived": 0,
                "is_pinned": 0
            })
            return conv_id
        except Exception as e:
            error_logger.error(f"MongoDB create_conversation error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (conv_id, title)
        )
        conn.commit()
        conn.close()
    return conv_id

def list_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    if is_mongo_active():
        try:
            db = get_mongo_db()
            docs = list(db.conversations.find({}, {"_id": 0}).sort([("is_pinned", -1), ("updated_at", -1)]).limit(limit))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB list_conversations error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations ORDER BY is_pinned DESC, updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows

def add_message(conversation_id: str, role: str, content: str, modality: str = "text", tokens: int = 0) -> str:
    msg_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            # 1. Guarantee conversation exists in database
            conv = db.conversations.find_one({"id": conversation_id})
            if not conv:
                title = (content[:45] + "...") if len(content) > 45 else content
                if not title.strip() or role == "assistant":
                    title = "New Chat Session"
                db.conversations.insert_one({
                    "id": conversation_id,
                    "title": title,
                    "created_at": now_str,
                    "updated_at": now_str,
                    "is_archived": 0,
                    "is_pinned": 0
                })
            else:
                db.conversations.update_one({"id": conversation_id}, {"$set": {"updated_at": now_str}})

            # 2. Insert message document
            db.messages.insert_one({
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "modality": modality,
                "tokens": tokens,
                "created_at": now_str
            })
            return msg_id
        except Exception as e:
            error_logger.error(f"MongoDB add_message error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Guarantee conversation exists in database
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            title = (content[:45] + "...") if len(content) > 45 else content
            if not title.strip() or role == "assistant":
                title = "New Chat Session"
            cursor.execute(
                "INSERT INTO conversations (id, title, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (conversation_id, title)
            )
        else:
            cursor.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )

        # 2. Insert message record
        cursor.execute(
            """INSERT INTO messages (id, conversation_id, role, content, modality, tokens)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (msg_id, conversation_id, role, content, modality, tokens)
        )
        conn.commit()
        conn.close()
    return msg_id

def get_conversation_messages(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    if is_mongo_active():
        try:
            db = get_mongo_db()
            docs = list(db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("created_at", 1).limit(limit))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB get_conversation_messages error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows

def delete_conversation(conversation_id: str) -> bool:
    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.messages.delete_many({"conversation_id": conversation_id})
            db.conversations.delete_one({"id": conversation_id})
            return True
        except Exception as e:
            error_logger.error(f"MongoDB delete_conversation error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        conn.close()
    return True

# ----------------- MEMORIES ----------------- #

def save_memory(key_text: str, value_text: str, category: str = "general", source: str = "chat", confidence: float = 1.0) -> str:
    mem_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            existing = db.memories.find_one({"key_text": key_text, "category": category})
            if existing:
                db.memories.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "value_text": value_text,
                        "source": source,
                        "confidence": confidence,
                        "updated_at": now_str
                    }}
                )
                return existing["id"]
            else:
                db.memories.insert_one({
                    "id": mem_id,
                    "category": category,
                    "key_text": key_text,
                    "value_text": value_text,
                    "source": source,
                    "confidence": confidence,
                    "created_at": now_str,
                    "updated_at": now_str
                })
                return mem_id
        except Exception as e:
            error_logger.error(f"MongoDB save_memory error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM memories WHERE key_text = ? AND category = ?", (key_text, category))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """UPDATE memories SET value_text = ?, source = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (value_text, source, confidence, existing["id"])
            )
            mem_id = existing["id"]
        else:
            cursor.execute(
                """INSERT INTO memories (id, category, key_text, value_text, source, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (mem_id, category, key_text, value_text, source, confidence)
            )
        conn.commit()
        conn.close()
    return mem_id

def search_memories(query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    if is_mongo_active():
        try:
            db = get_mongo_db()
            if query:
                q_regex = {"$regex": re.escape(query), "$options": "i"}
                filter_doc = {"$or": [{"key_text": q_regex}, {"value_text": q_regex}]}
            else:
                filter_doc = {}
            docs = list(db.memories.find(filter_doc, {"_id": 0}).sort("updated_at", -1).limit(limit))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB search_memories error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        if query:
            search_param = f"%{query}%"
            cursor.execute(
                """SELECT * FROM memories 
                   WHERE key_text LIKE ? OR value_text LIKE ? 
                   ORDER BY updated_at DESC LIMIT ?""",
                (search_param, search_param, limit)
            )
        else:
            cursor.execute("SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows

def delete_memory(mem_id: str) -> bool:
    if is_mongo_active():
        try:
            db = get_mongo_db()
            res = db.memories.delete_one({"id": mem_id})
            return res.deleted_count > 0
        except Exception as e:
            error_logger.error(f"MongoDB delete_memory error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
        affected = cursor.rowcount > 0
        conn.commit()
        conn.close()
    return affected

# ----------------- TOOL EXECUTIONS ----------------- #

def record_tool_execution(tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any], status: str, duration_ms: float = 0.0) -> str:
    exec_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.tool_executions.insert_one({
                "id": exec_id,
                "tool_name": tool_name,
                "parameters_json": json.dumps(parameters),
                "result_json": json.dumps(result),
                "status": status,
                "duration_ms": duration_ms,
                "created_at": now_str
            })
            return exec_id
        except Exception as e:
            error_logger.error(f"MongoDB record_tool_execution error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO tool_executions (id, tool_name, parameters_json, result_json, status, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (exec_id, tool_name, json.dumps(parameters), json.dumps(result), status, duration_ms)
        )
        conn.commit()
        conn.close()
    return exec_id

# ----------------- TRAINING SAMPLES ----------------- #

def add_training_example(raw_text: str, intent: str, entities: Optional[Dict[str, Any]] = None, confidence: float = 0.0, source: str = "user_interaction") -> str:
    ex_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.training_examples.insert_one({
                "id": ex_id,
                "raw_text": raw_text,
                "intent": intent,
                "entities_json": json.dumps(entities or {}),
                "confidence": confidence,
                "source": source,
                "approved": 0,
                "created_at": now_str
            })
            return ex_id
        except Exception as e:
            error_logger.error(f"MongoDB add_training_example error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO training_examples (id, raw_text, intent, entities_json, confidence, source, approved)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (ex_id, raw_text, intent, json.dumps(entities or {}), confidence, source)
        )
        conn.commit()
        conn.close()
    return ex_id

def get_training_examples(approved_only: bool = False) -> List[Dict[str, Any]]:
    if is_mongo_active():
        try:
            db = get_mongo_db()
            filter_doc = {"approved": 1} if approved_only else {}
            docs = list(db.training_examples.find(filter_doc, {"_id": 0}).sort("created_at", -1))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB get_training_examples error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        if approved_only:
            cursor.execute("SELECT * FROM training_examples WHERE approved = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM training_examples ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows


# ----------------- USERS & AUTHENTICATION ----------------- #

import hashlib
import secrets

def hash_password(password: str) -> str:
    """Secure PBKDF2-HMAC-SHA256 password hashing with random 16-byte salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${key}"

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plain password against the stored salt$hash format using constant-time comparison."""
    try:
        if not hashed or "$" not in hashed:
            return False
        salt, key = hashed.split("$", 1)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return secrets.compare_digest(key, new_key)
    except Exception as e:
        error_logger.warning(f"Password verification error: {e}")
        return False

def create_user(
    username: str,
    password: str,
    full_name: str,
    email: str = "",
    role: str = "user"
) -> Optional[Dict[str, Any]]:
    """Creates a new user record in MongoDB Atlas or SQLite."""
    user_id = str(uuid.uuid4())
    username_clean = username.strip().lower()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    pwd_hash = hash_password(password)

    # Check if username exists first
    existing = get_user_by_username(username_clean)
    if existing:
        return None

    user_doc = {
        "id": user_id,
        "username": username_clean,
        "email": email.strip() or f"{username_clean}@ajax.ai",
        "full_name": full_name.strip() or username_clean.title(),
        "password_hash": pwd_hash,
        "role": role if role in ["admin", "user"] else "user",
        "status": "active",
        "created_at": now_str,
        "last_login": now_str
    }

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.users.insert_one(user_doc)
            safe_doc = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_id"]}
            return safe_doc
        except Exception as e:
            error_logger.error(f"MongoDB create_user error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (id, username, email, full_name, password_hash, role, status, created_at, last_login)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                username_clean,
                user_doc["email"],
                user_doc["full_name"],
                pwd_hash,
                user_doc["role"],
                user_doc["status"],
                now_str,
                now_str
            )
        )
        conn.commit()
        conn.close()

    safe_doc = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_id"]}
    return safe_doc

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by username (including password_hash for authentication)."""
    username_clean = username.strip().lower()
    if is_mongo_active():
        try:
            db = get_mongo_db()
            doc = db.users.find_one({"username": username_clean}, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            error_logger.error(f"MongoDB get_user_by_username error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? LIMIT 1", (username_clean,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves user by ID without sensitive password hash."""
    if is_mongo_active():
        try:
            db = get_mongo_db()
            doc = db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
            if doc:
                return doc
        except Exception as e:
            error_logger.error(f"MongoDB get_user_by_id error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, full_name, role, status, created_at, last_login FROM users WHERE id = ? LIMIT 1", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    return None

def list_all_users() -> List[Dict[str, Any]]:
    """Lists all registered users without password hashes (Admin only)."""
    if is_mongo_active():
        try:
            db = get_mongo_db()
            docs = list(db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB list_all_users error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, full_name, role, status, created_at, last_login FROM users ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

def update_user_status(user_id: str, status: str) -> bool:
    """Toggles user active / blocked status."""
    if status not in ["active", "blocked"]:
        return False

    if is_mongo_active():
        try:
            db = get_mongo_db()
            res = db.users.update_one({"id": user_id}, {"$set": {"status": status}})
            return res.modified_count > 0
        except Exception as e:
            error_logger.error(f"MongoDB update_user_status error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

def update_user_role(user_id: str, role: str) -> bool:
    """Changes user role between admin and user."""
    if role not in ["admin", "user"]:
        return False

    if is_mongo_active():
        try:
            db = get_mongo_db()
            res = db.users.update_one({"id": user_id}, {"$set": {"role": role}})
            return res.modified_count > 0
        except Exception as e:
            error_logger.error(f"MongoDB update_user_role error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

def delete_user(user_id: str) -> bool:
    """Deletes a user account."""
    if is_mongo_active():
        try:
            db = get_mongo_db()
            res = db.users.delete_one({"id": user_id})
            return res.deleted_count > 0
        except Exception as e:
            error_logger.error(f"MongoDB delete_user error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

def update_user_last_login(user_id: str) -> bool:
    """Updates last login timestamp for a user."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.users.update_one({"id": user_id}, {"$set": {"last_login": now_str}})
            return True
        except Exception as e:
            error_logger.error(f"MongoDB update_user_last_login error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user_id))
        conn.commit()
        conn.close()
        return True

def seed_default_admin():
    """Seeds default administrator account (admin / admin123) if none exists."""
    admin_user = get_user_by_username("admin")
    if not admin_user:
        create_user(
            username="admin",
            password="admin123",
            full_name="Ajay Singh (Administrator)",
            email="admin@ajax.ai",
            role="admin"
        )
        ajax_logger.info("Default administrator account seeded: 'admin' / 'admin123'")

def seed_default_demo_user():
    """Seeds default demo user account (demo / demo123) if none exists."""
    demo_user = get_user_by_username("demo")
    if not demo_user:
        create_user(
            username="demo",
            password="demo123",
            full_name="Demo User",
            email="demo@ajax.ai",
            role="user"
        )
        ajax_logger.info("Default demo account seeded: 'demo' / 'demo123'")


