"""
AJAX AI - Database Connection & Initialization Engine
Unified support for PostgreSQL and SQLite with automatic migration and query abstraction.
"""

import os
import re
import sqlite3
import threading
from typing import Optional, Any, List, Dict
from core.logger import ajax_logger, error_logger
from config.config_loader import config

DB_LOCK = threading.Lock()
_IS_POSTGRES = False

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.extensions
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

class UniversalCursorWrapper:
    """Wraps SQLite / PostgreSQL cursor to provide uniform dictionary rows and query adaptation."""
    def __init__(self, cursor, is_postgres: bool = False):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def execute(self, sql: str, params: Any = None):
        if self.is_postgres and params is not None:
            # Convert SQLite ? placeholders to PostgreSQL %s placeholders
            sql = sql.replace("?", "%s")
        if params is not None:
            return self.cursor.execute(sql, params)
        return self.cursor.execute(sql)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        try:
            return dict(row)
        except Exception:
            return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return rows
        try:
            return [dict(r) for r in rows]
        except Exception:
            return rows

    def __getattr__(self, name):
        return getattr(self.cursor, name)

class UniversalConnectionWrapper:
    """Uniform connection wrapper for commit, close, cursor."""
    def __init__(self, conn, is_postgres: bool = False):
        self.conn = conn
        self.is_postgres = is_postgres

    def cursor(self):
        if self.is_postgres:
            return UniversalCursorWrapper(self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor), is_postgres=True)
        return UniversalCursorWrapper(self.conn.cursor(), is_postgres=False)

    def commit(self):
        return self.conn.commit()

    def rollback(self):
        return self.conn.rollback()

    def close(self):
        return self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

_PG_CHECKED = False
_PG_AVAILABLE = False

def _check_and_init_postgres(db_conf) -> bool:
    global _PG_CHECKED, _PG_AVAILABLE
    if not HAS_PSYCOPG2:
        return False
    try:
        # Check target database or URL
        if db_conf.postgres_url:
            test_conn = psycopg2.connect(db_conf.postgres_url, connect_timeout=2)
            test_conn.close()
            _PG_AVAILABLE = True
            return True
        
        # Try connecting to postgres
        try:
            m_conn = psycopg2.connect(
                host=db_conf.postgres_host,
                port=db_conf.postgres_port,
                user=db_conf.postgres_user,
                password=db_conf.postgres_password,
                dbname="postgres",
                connect_timeout=2
            )
            m_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = m_conn.cursor()
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_conf.postgres_db,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_conf.postgres_db}"')
                ajax_logger.info(f"Created PostgreSQL Database: '{db_conf.postgres_db}'")
            cur.close()
            m_conn.close()
            _PG_AVAILABLE = True
            return True
        except Exception:
            # Try connecting directly to db
            test_conn = psycopg2.connect(
                host=db_conf.postgres_host,
                port=db_conf.postgres_port,
                user=db_conf.postgres_user,
                password=db_conf.postgres_password,
                dbname=db_conf.postgres_db,
                connect_timeout=2
            )
            test_conn.close()
            _PG_AVAILABLE = True
            return True
    except Exception as e:
        ajax_logger.warning(f"PostgreSQL not currently reachable on {db_conf.postgres_host}:{db_conf.postgres_port}. Using high-speed SQLite.")
        _PG_AVAILABLE = False
        return False
    finally:
        _PG_CHECKED = True

def get_db_connection() -> UniversalConnectionWrapper:
    """Establishes connection to PostgreSQL (if reachable) or SQLite."""
    global _IS_POSTGRES, _PG_CHECKED, _PG_AVAILABLE
    db_conf = config.database
    use_postgres = db_conf.db_type.lower() in ["postgres", "postgresql", "pgsql"]

    if use_postgres and HAS_PSYCOPG2:
        if not _PG_CHECKED:
            _check_and_init_postgres(db_conf)

        if _PG_AVAILABLE:
            try:
                if db_conf.postgres_url:
                    raw_conn = psycopg2.connect(db_conf.postgres_url)
                else:
                    raw_conn = psycopg2.connect(
                        host=db_conf.postgres_host,
                        port=db_conf.postgres_port,
                        user=db_conf.postgres_user,
                        password=db_conf.postgres_password,
                        dbname=db_conf.postgres_db
                    )
                _IS_POSTGRES = True
                return UniversalConnectionWrapper(raw_conn, is_postgres=True)
            except Exception as e:
                _PG_AVAILABLE = False
                _IS_POSTGRES = False

    # SQLite fallback
    os.makedirs(os.path.dirname(config.database_path), exist_ok=True)
    raw_conn = sqlite3.connect(config.database_path, check_same_thread=False)
    raw_conn.row_factory = sqlite3.Row
    _IS_POSTGRES = False
    return UniversalConnectionWrapper(raw_conn, is_postgres=False)

    # SQLite fallback
    os.makedirs(os.path.dirname(config.database_path), exist_ok=True)
    raw_conn = sqlite3.connect(config.database_path, check_same_thread=False)
    raw_conn.row_factory = sqlite3.Row
    _IS_POSTGRES = False
    return UniversalConnectionWrapper(raw_conn, is_postgres=False)

def init_db():
    """Initialize all tables with proper schema for both PostgreSQL and SQLite."""
    with DB_LOCK:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            is_pg = conn.is_postgres

            # DDL Queries
            tables = [
                # 1. Conversations
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(64) PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_archived INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0
                )
                """,
                # 2. Messages
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id VARCHAR(64) PRIMARY KEY,
                    conversation_id VARCHAR(64) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    content TEXT NOT NULL,
                    modality VARCHAR(32) DEFAULT 'text',
                    tokens INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 3. Memories
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id VARCHAR(64) PRIMARY KEY,
                    category VARCHAR(64) DEFAULT 'general',
                    key_text TEXT NOT NULL,
                    value_text TEXT NOT NULL,
                    source VARCHAR(32) DEFAULT 'chat',
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 4. Tool Executions
                """
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id VARCHAR(64) PRIMARY KEY,
                    tool_name VARCHAR(128) NOT NULL,
                    parameters_json TEXT,
                    result_json TEXT,
                    status VARCHAR(32) NOT NULL,
                    duration_ms REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 5. Training Examples
                """
                CREATE TABLE IF NOT EXISTS training_examples (
                    id VARCHAR(64) PRIMARY KEY,
                    raw_text TEXT NOT NULL,
                    intent VARCHAR(64) NOT NULL,
                    entities_json TEXT,
                    confidence REAL DEFAULT 0.0,
                    source VARCHAR(64) DEFAULT 'user_interaction',
                    approved INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 6. Scheduled Tasks
                """
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id VARCHAR(64) PRIMARY KEY,
                    task_type VARCHAR(64) NOT NULL,
                    target_time VARCHAR(128) NOT NULL,
                    recurrence VARCHAR(64) DEFAULT 'none',
                    payload_json TEXT,
                    status VARCHAR(32) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 7. Audit Logs
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id VARCHAR(64) PRIMARY KEY,
                    event_type VARCHAR(64) NOT NULL,
                    severity VARCHAR(32) DEFAULT 'INFO',
                    details_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]

            for table_ddl in tables:
                cursor.execute(table_ddl)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_cat ON memories(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON scheduled_tasks(status)")

            conn.commit()
            conn.close()
            db_name = "PostgreSQL" if is_pg else "SQLite"
            ajax_logger.info(f"{db_name} Database initialized successfully with all tables.")
        except Exception as e:
            error_logger.error(f"Failed to initialize database: {e}")
            raise e
