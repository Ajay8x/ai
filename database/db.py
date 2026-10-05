"""
AJAX AI - Database Connection and Initialization Engine
Manages SQLite database connection, table migrations, and transactions.
"""

import sqlite3
import os
import threading
from typing import Optional
from core.logger import ajax_logger, error_logger
from config.config_loader import config

DB_LOCK = threading.Lock()

def get_db_connection():
    os.makedirs(os.path.dirname(config.database_path), exist_ok=True)
    conn = sqlite3.connect(config.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize all core database tables with proper indexing."""
    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 1. Conversations Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_archived INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0
            )
            """)
            
            # 2. Messages Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL, -- user, assistant, system, tool
                content TEXT NOT NULL,
                modality TEXT DEFAULT 'text', -- text, voice, image
                tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
            """)
            
            # 3. Memories Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT DEFAULT 'general', -- user_fact, preference, task, note
                key_text TEXT NOT NULL,
                value_text TEXT NOT NULL,
                source TEXT DEFAULT 'chat',
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 4. Tool Executions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                parameters_json TEXT,
                result_json TEXT,
                status TEXT NOT NULL, -- SUCCESS, ERROR, BLOCKED
                duration_ms REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 5. Training Examples Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_examples (
                id TEXT PRIMARY KEY,
                raw_text TEXT NOT NULL,
                intent TEXT NOT NULL,
                entities_json TEXT,
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'user_interaction',
                approved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 6. Model Registry Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_registry (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                model_type TEXT NOT NULL,
                accuracy REAL,
                f1_score REAL,
                file_path TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 7. Scheduled Tasks Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL, -- timer, alarm, reminder, system
                target_time TEXT NOT NULL,
                recurrence TEXT DEFAULT 'none',
                payload_json TEXT,
                status TEXT DEFAULT 'pending', -- pending, completed, cancelled
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 8. Audit Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT DEFAULT 'INFO',
                details_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Indexes for high performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_cat ON memories(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON scheduled_tasks(status)")
            
            conn.commit()
            conn.close()
            ajax_logger.info("Database initialized successfully with all tables.")
        except Exception as e:
            error_logger.error(f"Failed to initialize database: {e}")
            raise e
