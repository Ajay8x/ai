"""
AJAX AI - Database CRUD Operations
High-performance query abstractions for conversations, memories, tools, and tasks.
"""

import uuid
import json
from typing import List, Dict, Any, Optional
from database.db import get_db_connection, DB_LOCK
from core.logger import ajax_logger, error_logger

# ----------------- CONVERSATIONS & MESSAGES ----------------- #

def create_conversation(title: str = "New Conversation") -> str:
    conv_id = str(uuid.uuid4())
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
    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO messages (id, conversation_id, role, content, modality, tokens)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (msg_id, conversation_id, role, content, modality, tokens)
        )
        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
        conn.close()
    return msg_id

def get_conversation_messages(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
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

# ----------------- MEMORIES ----------------- #

def save_memory(key_text: str, value_text: str, category: str = "general", source: str = "chat", confidence: float = 1.0) -> str:
    mem_id = str(uuid.uuid4())
    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if key exists in category, update or insert
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
