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

try:
    import pymongo
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

_MONGO_CLIENT = None
_MONGO_CHECKED = False
_MONGO_AVAILABLE = False

def get_mongo_client() -> Optional[Any]:
    """Establishes or returns cached MongoDB Atlas client connection."""
    global _MONGO_CLIENT, _MONGO_CHECKED, _MONGO_AVAILABLE
    if not HAS_PYMONGO:
        return None
    if _MONGO_CLIENT is not None and _MONGO_AVAILABLE:
        return _MONGO_CLIENT
    
    uri = config.database.mongodb_uri
    if not uri:
        _MONGO_AVAILABLE = False
        return None
    
    try:
        if "retryWrites" not in uri and "?" not in uri:
            uri = f"{uri}/?retryWrites=true&w=majority"
        elif "retryWrites" not in uri and "?" in uri:
            uri = f"{uri}&retryWrites=true&w=majority"

        client = pymongo.MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=50
        )
        # Test connection ping
        client.admin.command('ping')
        _MONGO_CLIENT = client
        _MONGO_AVAILABLE = True
        return _MONGO_CLIENT
    except Exception as e:
        ajax_logger.warning(f"MongoDB Atlas connection check failed: {e}. Falling back to SQLite.")
        _MONGO_AVAILABLE = False
        return None
    finally:
        _MONGO_CHECKED = True

def get_mongo_db() -> Optional[Any]:
    """Returns the MongoDB database instance."""
    client = get_mongo_client()
    if client is not None:
        db_name = config.database.mongodb_db or "ajax_ai"
        return client[db_name]
    return None

def is_mongo_active() -> bool:
    """Returns True if MongoDB is configured and responsive."""
    global _MONGO_AVAILABLE, _MONGO_CHECKED
    if config.database.db_type.lower() != "mongodb" and not config.database.mongodb_uri:
        return False
    if not _MONGO_CHECKED:
        get_mongo_client()
    return _MONGO_AVAILABLE

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
        import socket
        # Ultra-fast socket check before trying heavy psycopg2 connection
        host = db_conf.postgres_host or "localhost"
        port = int(db_conf.postgres_port or 5432)
        try:
            with socket.create_connection((host, port), timeout=0.3):
                pass
        except Exception:
            ajax_logger.warning(f"PostgreSQL port {port} on {host} is closed. Using high-speed SQLite.")
            _PG_AVAILABLE = False
            return False

        # Check target database or URL
        if db_conf.postgres_url:
            test_conn = psycopg2.connect(db_conf.postgres_url, connect_timeout=1)
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

    # SQLite fallback (uses /tmp on Vercel Serverless environment)
    db_path = config.database_path
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        db_path = os.path.join("/tmp", "ajax_ai.db")
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except OSError:
        pass
    raw_conn = sqlite3.connect(db_path, check_same_thread=False)
    raw_conn.row_factory = sqlite3.Row
    _IS_POSTGRES = False
    return UniversalConnectionWrapper(raw_conn, is_postgres=False)


def _migrate_sqlite_to_mongo_if_needed(db):
    """Auto-migrates existing SQLite records to MongoDB Atlas if MongoDB collections are empty."""
    db_path = config.database_path
    if not os.path.exists(db_path):
        return
    try:
        if db.conversations.count_documents({}) > 0:
            ajax_logger.info("MongoDB Atlas already contains conversation data. Skipping auto-migration.")
            return

        ajax_logger.info(f"Found local SQLite database at {db_path}. Auto-migrating data to MongoDB Atlas...")
        sq_conn = sqlite3.connect(db_path)
        sq_conn.row_factory = sqlite3.Row
        cur = sq_conn.cursor()

        # Migrate conversations
        try:
            cur.execute("SELECT * FROM conversations")
            convs = [dict(r) for r in cur.fetchall()]
            if convs:
                db.conversations.insert_many(convs)
                ajax_logger.info(f"Migrated {len(convs)} conversations to MongoDB Atlas.")
        except Exception as e:
            ajax_logger.warning(f"Error migrating conversations: {e}")

        # Migrate messages
        try:
            cur.execute("SELECT * FROM messages")
            msgs = [dict(r) for r in cur.fetchall()]
            if msgs:
                db.messages.insert_many(msgs)
                ajax_logger.info(f"Migrated {len(msgs)} messages to MongoDB Atlas.")
        except Exception as e:
            ajax_logger.warning(f"Error migrating messages: {e}")

        # Migrate memories
        try:
            cur.execute("SELECT * FROM memories")
            mems = [dict(r) for r in cur.fetchall()]
            if mems:
                db.memories.insert_many(mems)
                ajax_logger.info(f"Migrated {len(mems)} memories to MongoDB Atlas.")
        except Exception as e:
            ajax_logger.warning(f"Error migrating memories: {e}")

        # Migrate tool_executions
        try:
            cur.execute("SELECT * FROM tool_executions")
            tools = [dict(r) for r in cur.fetchall()]
            if tools:
                db.tool_executions.insert_many(tools)
                ajax_logger.info(f"Migrated {len(tools)} tool execution logs to MongoDB Atlas.")
        except Exception as e:
            ajax_logger.warning(f"Error migrating tool executions: {e}")

        # Migrate training_examples
        try:
            cur.execute("SELECT * FROM training_examples")
            trainings = [dict(r) for r in cur.fetchall()]
            if trainings:
                db.training_examples.insert_many(trainings)
                ajax_logger.info(f"Migrated {len(trainings)} training examples to MongoDB Atlas.")
        except Exception as e:
            ajax_logger.warning(f"Error migrating training examples: {e}")

        sq_conn.close()
        ajax_logger.info("Successfully migrated existing local data into MongoDB Atlas!")
    except Exception as e:
        ajax_logger.warning(f"SQLite to MongoDB migration notice: {e}")


def init_db():
    """Initialize all tables/collections with proper schema for MongoDB Atlas, PostgreSQL, or SQLite."""
    with DB_LOCK:
        # 1. Check if MongoDB Atlas is active
        if is_mongo_active():
            try:
                db = get_mongo_db()
                ajax_logger.info(f"Initializing MongoDB Atlas collections and indexes for database '{db.name}'...")
                
                # Indexes
                db.conversations.create_index("id", unique=True)
                db.conversations.create_index([("is_pinned", -1), ("updated_at", -1)])
                
                db.messages.create_index("id", unique=True)
                db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
                
                db.memories.create_index("id", unique=True)
                db.memories.create_index([("category", 1), ("key_text", 1)])
                
                db.tool_executions.create_index("id", unique=True)
                db.tool_executions.create_index([("created_at", -1)])
                
                db.training_examples.create_index("id", unique=True)
                db.training_examples.create_index([("created_at", -1)])

                db.scheduled_tasks.create_index("id", unique=True)
                db.scheduled_tasks.create_index([("status", 1)])

                db.audit_logs.create_index("id", unique=True)
                db.audit_logs.create_index([("created_at", -1)])

                # Public API Connectors & Loop Subsystem
                db.api_providers.create_index("id", unique=True)
                db.api_providers.create_index("category")
                db.api_usage.create_index([("provider_id", 1), ("timestamp", -1)])
                db.api_health_checks.create_index([("provider_id", 1), ("checked_at", -1)])
                db.connector_schemas.create_index("id", unique=True)
                db.connector_schemas.create_index("provider_id")
                db.api_cache_metadata.create_index("cache_key", unique=True)
                db.scheduled_jobs.create_index("id", unique=True)
                db.workflow_dependencies.create_index([("source_node", 1), ("target_node", 1)])
                db.loop_detection_events.create_index([("created_at", -1)])
                db.api_audit_logs.create_index([("created_at", -1)])

                # Auto-migrate SQLite data if MongoDB Atlas collections are empty
                _migrate_sqlite_to_mongo_if_needed(db)
                ajax_logger.info("MongoDB Atlas initialized successfully with all collections and indexes.")
                return
            except Exception as e:
                ajax_logger.error(f"Failed to initialize MongoDB Atlas: {e}. Falling back to SQLite.")

        # 2. SQLite / PostgreSQL Initialization
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
                """,
                # 8. API Providers Registry
                """
                CREATE TABLE IF NOT EXISTS api_providers (
                    id VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    category VARCHAR(64) NOT NULL,
                    official_docs_url TEXT,
                    base_url TEXT NOT NULL,
                    auth_type VARCHAR(32) DEFAULT 'none',
                    required_credentials TEXT,
                    rate_limit_rpm INTEGER DEFAULT 60,
                    quota_daily INTEGER,
                    commercial_use VARCHAR(32) DEFAULT 'unknown',
                    license_url TEXT,
                    attribution TEXT,
                    cors_status VARCHAR(32) DEFAULT 'unknown',
                    backend_proxy_required INTEGER DEFAULT 1,
                    default_timeout INTEGER DEFAULT 10,
                    retry_max INTEGER DEFAULT 3,
                    cache_ttl_sec INTEGER DEFAULT 300,
                    data_classification VARCHAR(32) DEFAULT 'live',
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 9. API Credentials (Encrypted/Redacted Store)
                """
                CREATE TABLE IF NOT EXISTS api_credentials (
                    id VARCHAR(64) PRIMARY KEY,
                    provider_id VARCHAR(64) NOT NULL,
                    key_name VARCHAR(128) NOT NULL,
                    encrypted_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 10. API Usage Metrics
                """
                CREATE TABLE IF NOT EXISTS api_usage (
                    id VARCHAR(64) PRIMARY KEY,
                    provider_id VARCHAR(64) NOT NULL,
                    endpoint TEXT NOT NULL,
                    status_code INTEGER,
                    latency_ms REAL,
                    tokens_or_units INTEGER DEFAULT 1,
                    caller_id VARCHAR(64),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 11. API Health Checks & Circuit Breakers
                """
                CREATE TABLE IF NOT EXISTS api_health_checks (
                    id VARCHAR(64) PRIMARY KEY,
                    provider_id VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    latency_ms REAL,
                    status_code INTEGER,
                    error_message TEXT,
                    circuit_breaker_state VARCHAR(32) DEFAULT 'CLOSED',
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 12. Dynamic Connector Schemas
                """
                CREATE TABLE IF NOT EXISTS connector_schemas (
                    id VARCHAR(64) PRIMARY KEY,
                    provider_id VARCHAR(64) NOT NULL,
                    schema_name VARCHAR(128) NOT NULL,
                    endpoint_path TEXT,
                    data_path TEXT,
                    fields_json TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 13. API Cache Metadata (ETag / Conditional Requests)
                """
                CREATE TABLE IF NOT EXISTS api_cache_metadata (
                    cache_key VARCHAR(128) PRIMARY KEY,
                    provider_id VARCHAR(64) NOT NULL,
                    etag VARCHAR(128),
                    last_modified VARCHAR(128),
                    response_body TEXT,
                    content_type VARCHAR(64),
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 14. Scheduled Refresh Jobs
                """
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id VARCHAR(64) PRIMARY KEY,
                    provider_id VARCHAR(64),
                    job_name VARCHAR(128) NOT NULL,
                    cron_expression VARCHAR(64),
                    interval_seconds INTEGER DEFAULT 300,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    status VARCHAR(32) DEFAULT 'active',
                    is_locked INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 15. Workflow Dependencies (DAG Graph for Cycle Detection)
                """
                CREATE TABLE IF NOT EXISTS workflow_dependencies (
                    id VARCHAR(64) PRIMARY KEY,
                    workflow_id VARCHAR(64) NOT NULL,
                    source_node VARCHAR(128) NOT NULL,
                    target_node VARCHAR(128) NOT NULL,
                    condition_expr TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 16. Loop Detection Events
                """
                CREATE TABLE IF NOT EXISTS loop_detection_events (
                    id VARCHAR(64) PRIMARY KEY,
                    loop_type VARCHAR(64) NOT NULL,
                    identifier VARCHAR(256) NOT NULL,
                    details_json TEXT,
                    severity VARCHAR(32) DEFAULT 'HIGH',
                    action_taken VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # 17. API Audit Logs
                """
                CREATE TABLE IF NOT EXISTS api_audit_logs (
                    id VARCHAR(64) PRIMARY KEY,
                    action VARCHAR(64) NOT NULL,
                    actor VARCHAR(64) DEFAULT 'system',
                    resource_type VARCHAR(64) NOT NULL,
                    resource_id VARCHAR(128),
                    sanitized_payload TEXT,
                    ip_address VARCHAR(45),
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_prov_cat ON api_providers(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_prov ON api_usage(provider_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_health_prov ON api_health_checks(provider_id, checked_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conn_schemas_prov ON connector_schemas(provider_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_loop_events_created ON loop_detection_events(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_audit_created ON api_audit_logs(created_at)")

            conn.commit()
            conn.close()
            db_name = "PostgreSQL" if is_pg else "SQLite"
            ajax_logger.info(f"{db_name} Database initialized successfully with all tables.")
        except Exception as e:
            error_logger.error(f"Failed to initialize database: {e}")
            raise e
