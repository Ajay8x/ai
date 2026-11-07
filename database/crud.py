"""
AJAX AI - Database CRUD Operations
High-performance query abstractions for conversations, memories, tools, and tasks.
Seamlessly unifies MongoDB Atlas (Cloud) with PostgreSQL and SQLite (Local fallback).
"""

import uuid
import json
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from database.db import get_db_connection, get_mongo_db, is_mongo_active, DB_LOCK, SYSTEM_SCOPE
from core.logger import ajax_logger, error_logger
from config.config_loader import config

# ----------------- CONVERSATIONS & MESSAGES ----------------- #

def _scope(user_id: Optional[str]) -> str:
    """Return a non-empty ownership scope for legacy/system callers."""
    return str(user_id or SYSTEM_SCOPE)


def _user_scope_filter(user_id: Optional[str]) -> Dict[str, Any]:
    """Matches the user's specific records as well as unassigned/system records for full session continuity."""
    if not user_id:
        return {"$or": [{"user_id": SYSTEM_SCOPE}, {"user_id": None}]}
    return {"$or": [{"user_id": str(user_id)}, {"user_id": SYSTEM_SCOPE}, {"user_id": None}]}


def get_conversation(conversation_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return a conversation only when it belongs to the requested scope or legacy unassigned pool."""
    owner_id = _scope(user_id)
    if is_mongo_active():
        try:
            db = get_mongo_db()
            doc = db.conversations.find_one(
                {"id": conversation_id, "$or": [{"user_id": owner_id}, {"user_id": None}, {"user_id": SYSTEM_SCOPE}]},
                {"_id": 0}
            )
            # If doc exists and was unassigned, associate it with this user so they own it
            if doc and user_id and doc.get("user_id") != owner_id:
                db.conversations.update_one({"id": conversation_id}, {"$set": {"user_id": owner_id}})
                doc["user_id"] = owner_id
            return doc
        except Exception as e:
            error_logger.error(f"MongoDB get_conversation error: {e}")
    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ? AND (user_id = ? OR user_id IS NULL OR user_id = ?)",
            (conversation_id, owner_id, SYSTEM_SCOPE)
        )
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None


def create_conversation(title: str = "New Conversation", user_id: Optional[str] = None, conversation_id: Optional[str] = None) -> str:
    conv_id = str(conversation_id or uuid.uuid4())
    owner_id = _scope(user_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.conversations.update_one(
                {"id": conv_id},
                {"$setOnInsert": {
                    "id": conv_id,
                    "user_id": owner_id,
                    "title": title,
                    "created_at": now_str,
                    "updated_at": now_str,
                    "is_archived": 0,
                    "is_pinned": 0
                }},
                upsert=True
            )
            return conv_id
        except Exception as e:
            error_logger.error(f"MongoDB create_conversation error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
                (conv_id, owner_id, title)
            )
            conn.commit()
        conn.close()
    return conv_id

def list_conversations(limit: int = 50, user_id: Optional[str] = None, include_all: bool = False) -> List[Dict[str, Any]]:
    owner_id = _scope(user_id)
    mongo_filter = {} if include_all else _user_scope_filter(user_id)
    if is_mongo_active():
        try:
            db = get_mongo_db()
            docs = list(db.conversations.find(mongo_filter, {"_id": 0}).sort([("is_pinned", -1), ("updated_at", -1)]).limit(limit))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB list_conversations error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        if include_all:
            cursor.execute("SELECT * FROM conversations ORDER BY is_pinned DESC, updated_at DESC LIMIT ?", (limit,))
        else:
            cursor.execute(
                "SELECT * FROM conversations WHERE user_id = ? OR user_id IS NULL OR user_id = ? ORDER BY is_pinned DESC, updated_at DESC LIMIT ?",
                (owner_id, SYSTEM_SCOPE, limit)
            )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows

def add_message(conversation_id: str, role: str, content: str, modality: str = "text", tokens: int = 0, user_id: Optional[str] = None) -> str:
    msg_id = str(uuid.uuid4())
    owner_id = _scope(user_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            # 1. Guarantee conversation exists in database and update ownership
            conv = db.conversations.find_one({"id": conversation_id})
            if not conv:
                title = (content[:45] + "...") if len(content) > 45 else content
                if not title.strip() or role == "assistant":
                    title = "New Chat Session"
                db.conversations.insert_one({
                    "id": conversation_id,
                    "user_id": owner_id,
                    "title": title,
                    "created_at": now_str,
                    "updated_at": now_str,
                    "is_archived": 0,
                    "is_pinned": 0
                })
            else:
                update_fields = {"updated_at": now_str}
                if user_id and conv.get("user_id") in (None, SYSTEM_SCOPE):
                    update_fields["user_id"] = owner_id
                db.conversations.update_one({"id": conversation_id}, {"$set": update_fields})

            # 2. Insert message document
            db.messages.insert_one({
                "id": msg_id,
                "user_id": owner_id,
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
        cursor.execute("SELECT id, user_id FROM conversations WHERE id = ?", (conversation_id,))
        existing_conv = cursor.fetchone()
        if not existing_conv:
            title = (content[:45] + "...") if len(content) > 45 else content
            if not title.strip() or role == "assistant":
                title = "New Chat Session"
            cursor.execute(
                "INSERT INTO conversations (id, user_id, title, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (conversation_id, owner_id, title)
            )
        else:
            if user_id and (existing_conv["user_id"] is None or existing_conv["user_id"] == SYSTEM_SCOPE):
                cursor.execute(
                    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP, user_id = ? WHERE id = ?",
                    (owner_id, conversation_id)
                )
            else:
                cursor.execute(
                    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (conversation_id,)
                )

        # 2. Insert message record
        cursor.execute(
            """INSERT INTO messages (id, user_id, conversation_id, role, content, modality, tokens)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, owner_id, conversation_id, role, content, modality, tokens)
        )
        conn.commit()
        conn.close()
    return msg_id

def get_conversation_messages(conversation_id: str, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    owner_id = _scope(user_id)
    if is_mongo_active():
        try:
            db = get_mongo_db()
            query_filter = {"conversation_id": conversation_id}
            if user_id:
                query_filter["$or"] = [{"user_id": owner_id}, {"user_id": None}, {"user_id": SYSTEM_SCOPE}]
            docs = list(db.messages.find(query_filter, {"_id": 0}).sort("created_at", 1).limit(limit))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB get_conversation_messages error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? AND (user_id = ? OR user_id IS NULL OR user_id = ?) ORDER BY created_at ASC LIMIT ?",
            (conversation_id, owner_id, SYSTEM_SCOPE, limit)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows

def delete_conversation(conversation_id: str, user_id: Optional[str] = None) -> bool:
    owner_id = _scope(user_id)
    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.messages.delete_many({"conversation_id": conversation_id, "user_id": owner_id})
            result = db.conversations.delete_one({"id": conversation_id, "user_id": owner_id})
            return result.deleted_count > 0
        except Exception as e:
            error_logger.error(f"MongoDB delete_conversation error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ? AND user_id = ?", (conversation_id, owner_id))
        cursor.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, owner_id))
        affected = cursor.rowcount > 0
        conn.commit()
        conn.close()
    return affected

# ----------------- MEMORIES ----------------- #

def save_memory(key_text: str, value_text: str, category: str = "general", source: str = "chat", confidence: float = 1.0, user_id: Optional[str] = None) -> str:
    mem_id = str(uuid.uuid4())
    owner_id = _scope(user_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            existing = db.memories.find_one({
                "$or": [{"user_id": owner_id}, {"user_id": None}, {"user_id": SYSTEM_SCOPE}],
                "key_text": key_text,
                "category": category
            })
            if existing:
                db.memories.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "value_text": value_text,
                        "source": source,
                        "confidence": confidence,
                        "user_id": owner_id,
                        "updated_at": now_str
                    }}
                )
                return existing.get("id", mem_id)
            else:
                db.memories.insert_one({
                    "id": mem_id,
                    "user_id": owner_id,
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
        cursor.execute("SELECT id FROM memories WHERE (user_id = ? OR user_id IS NULL OR user_id = ?) AND key_text = ? AND category = ?", (owner_id, SYSTEM_SCOPE, key_text, category))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """UPDATE memories SET value_text = ?, source = ?, confidence = ?, user_id = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (value_text, source, confidence, owner_id, existing["id"])
            )
            mem_id = existing["id"]
        else:
            cursor.execute(
                """INSERT INTO memories (id, user_id, category, key_text, value_text, source, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (mem_id, owner_id, category, key_text, value_text, source, confidence)
            )
        conn.commit()
        conn.close()
    return mem_id

def search_memories(query: str = "", limit: int = 10, user_id: Optional[str] = None, include_all: bool = False) -> List[Dict[str, Any]]:
    owner_id = _scope(user_id)
    user_cond = {} if include_all else _user_scope_filter(user_id)

    # Extract meaningful keywords from query
    tokens = [t.lower() for t in re.findall(r'[\w\u0900-\u097F]+', query or "")]
    stopwords = {
        "kya", "hai", "ka", "ki", "ke", "ko", "me", "se", "aur", "ye", "wo", "batao", "mujhe", "mera", "meri", "mere",
        "what", "is", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "my",
        "tell", "me", "you", "your", "who", "where", "how", "when", "do", "does", "did", "please"
    }
    keywords = [t for t in tokens if t not in stopwords and len(t) >= 2]

    if is_mongo_active():
        try:
            db = get_mongo_db()
            filter_doc = user_cond
            if keywords:
                keyword_regexes = [{"$regex": re.escape(kw), "$options": "i"} for kw in keywords]
                field_conditions = []
                for kr in keyword_regexes:
                    field_conditions.append({"key_text": kr})
                    field_conditions.append({"value_text": kr})
                    field_conditions.append({"category": kr})
                filter_doc = {"$and": [user_cond, {"$or": field_conditions}]}
            elif query.strip():
                q_regex = {"$regex": re.escape(query.strip()), "$options": "i"}
                filter_doc = {"$and": [user_cond, {"$or": [{"key_text": q_regex}, {"value_text": q_regex}]}]}

            docs = list(db.memories.find(filter_doc, {"_id": 0}).sort("updated_at", -1).limit(limit))
            # Fallback to general user memories if specific query didn't match
            if not docs and query.strip():
                docs = list(db.memories.find(user_cond, {"_id": 0}).sort("updated_at", -1).limit(limit))
            return docs
        except Exception as e:
            error_logger.error(f"MongoDB search_memories error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        if keywords:
            search_param = f"%{keywords[0]}%"
            cursor.execute(
                """SELECT * FROM memories
                   WHERE (user_id = ? OR user_id IS NULL OR user_id = ?) AND (key_text LIKE ? OR value_text LIKE ?)
                   ORDER BY updated_at DESC LIMIT ?""",
                (owner_id, SYSTEM_SCOPE, search_param, search_param, limit)
            )
        elif query.strip():
            search_param = f"%{query.strip()}%"
            cursor.execute(
                """SELECT * FROM memories
                   WHERE (user_id = ? OR user_id IS NULL OR user_id = ?) AND (key_text LIKE ? OR value_text LIKE ?)
                   ORDER BY updated_at DESC LIMIT ?""",
                (owner_id, SYSTEM_SCOPE, search_param, search_param, limit)
            )
        else:
            if include_all:
                cursor.execute("SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM memories WHERE user_id = ? OR user_id IS NULL OR user_id = ? ORDER BY updated_at DESC LIMIT ?", (owner_id, SYSTEM_SCOPE, limit))
        rows = [dict(row) for row in cursor.fetchall()]
        if not rows and query.strip():
            cursor.execute("SELECT * FROM memories WHERE user_id = ? OR user_id IS NULL OR user_id = ? ORDER BY updated_at DESC LIMIT ?", (owner_id, SYSTEM_SCOPE, limit))
            rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return rows

def get_cross_session_context(
    query: str,
    user_id: Optional[str] = None,
    current_conversation_id: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    Assembles long-term memory and relevant past session history from MongoDB Atlas.
    Guarantees cross-session continuity so the AI assistant never forgets past interactions.
    """
    owner_id = _scope(user_id)
    sections = []

    # 1. User Profile & Learned Facts from db.memories
    memories = search_memories(query=query, limit=8, user_id=user_id)
    if memories:
        mem_lines = []
        for m in memories:
            k = m.get("key_text", "").replace("_", " ").title()
            v = m.get("value_text", "")
            mem_lines.append(f"- {k}: {v}")
        sections.append("### 🧠 Learned User Facts & Long-Term Memory (from MongoDB Atlas):\n" + "\n".join(mem_lines))

    # 2. Check if user is asking about previous sessions or topics discussed earlier
    q_lower = query.lower()
    past_session_triggers = [
        "pehle", "pichle", "pichli", "kal", "purane", "previous", "earlier", "past session",
        "last time", "yaad", "remember", "kya baat hui thi", "maine kya pucha tha", "kya bola tha",
        "history", "what did we discuss", "what did i say", "humne kya"
    ]
    is_asking_past = any(t in q_lower for t in past_session_triggers)

    # 3. Search past conversations and QA history in MongoDB Atlas
    if is_mongo_active():
        try:
            db = get_mongo_db()
            user_cond = _user_scope_filter(user_id)

            # If user explicitly asks about past chats, fetch the recent sessions
            if is_asking_past:
                conv_filter = {**user_cond}
                if current_conversation_id:
                    conv_filter["id"] = {"$ne": current_conversation_id}

                recent_convs = list(db.conversations.find(conv_filter, {"_id": 0}).sort("updated_at", -1).limit(4))
                if recent_convs:
                    conv_snippets = []
                    for c in recent_convs:
                        cid = c.get("id")
                        title = c.get("title", "Chat Session")
                        date = c.get("updated_at", "")
                        last_msgs = list(db.messages.find({"conversation_id": cid}, {"_id": 0, "role": 1, "content": 1}).sort("created_at", -1).limit(2))
                        last_msgs.reverse()
                        summary_parts = [f"  * {m['role'].capitalize()}: {m['content'][:140]}..." for m in last_msgs if m.get("content")]
                        summary_str = "\n".join(summary_parts) if summary_parts else "  * (Discussion session)"
                        conv_snippets.append(f"• Session '{title}' ({date}):\n{summary_str}")
                    if conv_snippets:
                        sections.append("### 📜 Recent Past Sessions Overview (from MongoDB Atlas):\n" + "\n\n".join(conv_snippets))

            # Also search for topic-specific past Q&As if query has specific keywords
            tokens = [t.lower() for t in re.findall(r'[\w\u0900-\u097F]+', query)]
            stopwords = {"kya", "hai", "ka", "ki", "ke", "ko", "me", "se", "aur", "ye", "wo", "what", "is", "the", "a", "tell", "me", "how"}
            keywords = [t for t in tokens if t not in stopwords and len(t) >= 3]

            if keywords:
                regex_list = [{"query": {"$regex": re.escape(kw), "$options": "i"}} for kw in keywords]
                regex_list += [{"response": {"$regex": re.escape(kw), "$options": "i"}} for kw in keywords]
                qa_filter = {"$and": [user_cond, {"$or": regex_list}]}
                past_qas = list(db.qa_history.find(qa_filter, {"_id": 0, "query": 1, "response": 1, "timestamp": 1}).sort("timestamp", -1).limit(3))
                if past_qas:
                    qa_snippets = []
                    for qa in past_qas:
                        q_snippet = qa.get("query", "")[:120]
                        r_snippet = qa.get("response", "")[:160]
                        qa_snippets.append(f"- User previously asked: '{q_snippet}' &rarr; Assistant: '{r_snippet}...'")
                    sections.append("### 🔍 Relevant Past Interactions Matching This Topic (from MongoDB Atlas):\n" + "\n".join(qa_snippets))

        except Exception as e:
            error_logger.warning(f"Error fetching cross-session MongoDB context: {e}")

    return "\n\n".join(sections)
    return rows

def delete_memory(mem_id: str, user_id: Optional[str] = None) -> bool:
    owner_id = _scope(user_id)
    if is_mongo_active():
        try:
            db = get_mongo_db()
            res = db.memories.delete_one({"id": mem_id, "user_id": owner_id})
            return res.deleted_count > 0
        except Exception as e:
            error_logger.error(f"MongoDB delete_memory error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (mem_id, owner_id))
        affected = cursor.rowcount > 0
        conn.commit()
        conn.close()
    return affected

# ----------------- TOOL EXECUTIONS ----------------- #

def record_tool_execution(tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any], status: str, duration_ms: float = 0.0, user_id: Optional[str] = None) -> str:
    exec_id = str(uuid.uuid4())
    owner_id = _scope(user_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.tool_executions.insert_one({
                "id": exec_id,
                "user_id": owner_id,
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
            """INSERT INTO tool_executions (id, user_id, tool_name, parameters_json, result_json, status, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (exec_id, owner_id, tool_name, json.dumps(parameters), json.dumps(result), status, duration_ms)
        )
        conn.commit()
        conn.close()
    return exec_id

# ----------------- TRAINING SAMPLES ----------------- #

def add_training_example(raw_text: str, intent: str, entities: Optional[Dict[str, Any]] = None, confidence: float = 0.0, source: str = "user_interaction", user_id: Optional[str] = None) -> str:
    ex_id = str(uuid.uuid4())
    owner_id = _scope(user_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Automatically approve confident user interactions for continuous learning
    # so every single chat makes the neural intent model and LLM smarter!
    is_approved = 1 if (confidence >= 0.60 or source in ("user_interaction", "voice_command", "web_stream", "api", "manual")) else 0

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.training_examples.insert_one({
                "id": ex_id,
                "user_id": owner_id,
                "raw_text": raw_text,
                "intent": intent,
                "entities_json": json.dumps(entities or {}),
                "confidence": confidence,
                "source": source,
                "approved": is_approved,
                "created_at": now_str
            })
            return ex_id
        except Exception as e:
            error_logger.error(f"MongoDB add_training_example error: {e}")

    with DB_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO training_examples (id, user_id, raw_text, intent, entities_json, confidence, source, approved)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ex_id, owner_id, raw_text, intent, json.dumps(entities or {}), confidence, source, is_approved)
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


def backfill_legacy_records_to_admin():
    """Associates all legacy unassigned conversations, messages, and training samples with the primary administrator."""
    username = config.admin_username.strip().lower()
    admin_user = get_user_by_username(username)
    if not admin_user:
        return
    admin_id = admin_user["id"]

    if is_mongo_active():
        try:
            db = get_mongo_db()
            unassigned_filter = {"$or": [{"user_id": None}, {"user_id": SYSTEM_SCOPE}]}
            r_c = db.conversations.update_many(unassigned_filter, {"$set": {"user_id": admin_id}})
            r_m = db.messages.update_many(unassigned_filter, {"$set": {"user_id": admin_id}})
            r_q = db.qa_history.update_many(unassigned_filter, {"$set": {"user_id": admin_id}})
            r_t = db.training_examples.update_many(unassigned_filter, {"$set": {"user_id": admin_id, "approved": 1}})
            r_mem = db.memories.update_many(unassigned_filter, {"$set": {"user_id": admin_id}})
            if r_c.modified_count > 0 or r_m.modified_count > 0:
                ajax_logger.info(f"Associated {r_c.modified_count} sessions and {r_m.modified_count} messages to administrator ({admin_id}).")
        except Exception as e:
            error_logger.warning(f"Mongo legacy backfill notice: {e}")

    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE conversations SET user_id = ? WHERE user_id IS NULL OR user_id = ?", (admin_id, SYSTEM_SCOPE))
            cursor.execute("UPDATE messages SET user_id = ? WHERE user_id IS NULL OR user_id = ?", (admin_id, SYSTEM_SCOPE))
            cursor.execute("UPDATE training_examples SET user_id = ?, approved = 1 WHERE user_id IS NULL OR user_id = ?", (admin_id, SYSTEM_SCOPE))
            cursor.execute("UPDATE memories SET user_id = ? WHERE user_id IS NULL OR user_id = ?", (admin_id, SYSTEM_SCOPE))
            conn.commit()
            conn.close()
        except Exception as e:
            error_logger.warning(f"SQLite legacy backfill notice: {e}")


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
    """Seeds an administrator only when a strong environment password is configured."""
    username = config.admin_username.strip().lower()
    password = config.admin_password
    if not username or len(password) < 12 or password.lower() in {"admin123", "password", "changeme"}:
        ajax_logger.warning("Administrator seeding skipped: set a strong ADMIN_PASSWORD (12+ characters).")
        return

    admin_user = get_user_by_username(username)
    if not admin_user:
        create_user(
            username=username,
            password=password,
            full_name="Ajay Singh (Administrator)",
            email=f"{username}@ajax.ai",
            role="admin"
        )
        ajax_logger.info("Configured administrator account seeded from environment settings.")

def seed_default_demo_user():
    """Seeds a demo user only when explicitly enabled with a strong password."""
    if not config.demo_login_enabled:
        return

    username = config.demo_username.strip().lower()
    password = config.demo_password
    if not username or len(password) < 12:
        ajax_logger.warning("Demo user seeding skipped: set a strong DEMO_PASSWORD (12+ characters).")
        return

    demo_user = get_user_by_username(username)
    if not demo_user:
        create_user(
            username=username,
            password=password,
            full_name="Demo User",
            email=f"{username}@ajax.ai",
            role="user"
        )
        ajax_logger.info("Configured demo account seeded from environment settings.")


# ----------------- PERSISTENT AUTH SESSIONS ----------------- #

def _session_token_hash(token: str) -> str:
    """Store only a one-way digest of bearer tokens in persistent storage."""
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def save_auth_session(token: str, user: Dict[str, Any], expires_at: float) -> bool:
    """Persists auth session to database so user remains logged in across server restarts."""
    user_id = user["id"]
    username = user["username"]
    role = user.get("role", "user")
    full_name = user.get("full_name", username)
    token_digest = _session_token_hash(token)

    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.auth_sessions.replace_one(
                {"token": token_digest},
                {
                    "token": token_digest,
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "full_name": full_name,
                    "expires_at": expires_at,
                    "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                },
                upsert=True
            )
            return True
        except Exception as e:
            error_logger.error(f"MongoDB save_auth_session error: {e}")

    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO auth_sessions (token, user_id, username, role, full_name, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                    user_id=excluded.user_id,
                    username=excluded.username,
                    role=excluded.role,
                    full_name=excluded.full_name,
                    expires_at=excluded.expires_at
                """,
                (token_digest, user_id, username, role, full_name, expires_at)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            error_logger.error(f"DB save_auth_session error: {e}")
            return False

def get_auth_session(token: str) -> Optional[Dict[str, Any]]:
    """Retrieves session from DB if valid and not expired."""
    import time
    now_ts = time.time()
    token_digest = _session_token_hash(token)

    if is_mongo_active():
        try:
            db = get_mongo_db()
            doc = db.auth_sessions.find_one({"token": token_digest, "expires_at": {"$gt": now_ts}}, {"_id": 0})
            return doc
        except Exception as e:
            error_logger.error(f"MongoDB get_auth_session error: {e}")

    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM auth_sessions WHERE token = ? AND expires_at > ?",
                (token_digest, now_ts)
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            error_logger.error(f"DB get_auth_session error: {e}")
            return None

def delete_auth_session(token: str) -> bool:
    """Deletes an auth session on logout."""
    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.auth_sessions.delete_one({"token": _session_token_hash(token)})
            return True
        except Exception as e:
            error_logger.error(f"MongoDB delete_auth_session error: {e}")

    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auth_sessions WHERE token = ?", (_session_token_hash(token),))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            error_logger.error(f"DB delete_auth_session error: {e}")
            return False


def purge_expired_auth_sessions() -> int:
    """Remove expired persistent sessions from the active auth store."""
    now_ts = time.time()

    if is_mongo_active():
        try:
            result = get_mongo_db().auth_sessions.delete_many({"expires_at": {"$lte": now_ts}})
            return int(result.deleted_count)
        except Exception as e:
            error_logger.warning(f"MongoDB purge_expired_auth_sessions notice: {e}")

    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (now_ts,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return int(deleted or 0)
        except Exception as e:
            error_logger.warning(f"DB purge_expired_auth_sessions notice: {e}")
            return 0


