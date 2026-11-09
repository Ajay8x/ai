"""
AJAX AI - Configuration Manager
Loads environment variables, default configurations, and allows dynamic runtime settings.
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Only these runtime preferences may be persisted. Provider credentials,
# database passwords, cloud secrets, and auth material must remain in the
# process environment or an external secret manager.
PERSISTED_LLM_FIELDS = (
    "provider",
    "model",
    "temperature",
    "max_tokens",
    "cpu_threads",
    "local_model_path",
    "thinking_mode",
)

try:
    os.makedirs(DATA_DIR, exist_ok=True)
except OSError:
    pass

def load_dotenv_simple(env_path: str):
    """Simple .env parser without external dependencies."""
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        print(f"Error loading .env: {e}")

# Load .env if present
load_dotenv_simple(os.path.join(BASE_DIR, ".env"))
if not os.path.exists(os.path.join(BASE_DIR, ".env")) and os.path.exists(os.path.join(BASE_DIR, ".env.example")):
    load_dotenv_simple(os.path.join(BASE_DIR, ".env.example"))

@dataclass
class LLMConfig:
    provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "ajax_local")
    model: str = os.getenv("LLM_MODEL", "ajax-native-100-intents")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    cpu_threads: int = int(os.getenv("CPU_THREADS", "12"))
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    local_model_path: str = os.getenv("LOCAL_MODEL_PATH", "")
    thinking_mode: bool = os.getenv("LLM_THINKING_MODE", "false").lower() == "true"

@dataclass
class VoiceConfig:
    enabled: bool = os.getenv("VOICE_ENABLED", "true").lower() == "true"
    wake_word: str = os.getenv("WAKE_WORD", "ajax")
    wake_word_enabled: bool = os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"
    tts_engine: str = os.getenv("TTS_ENGINE", "pyttsx3")
    stt_engine: str = os.getenv("STT_ENGINE", "speech_recognition")
    stt_language: str = os.getenv("STT_LANGUAGE", "en-IN")
    stt_fallback_languages: str = os.getenv("STT_FALLBACK_LANGUAGES", "hi-IN")
    rate: int = int(os.getenv("VOICE_RATE", "180"))
    volume: float = float(os.getenv("VOICE_VOLUME", "1.0"))

@dataclass
class SafetyConfig:
    level: str = os.getenv("SAFETY_LEVEL", "STANDARD") # STANDARD, STRICT, PERMISSIVE
    require_confirmation: bool = os.getenv("REQUIRE_CONFIRMATION_FOR_DESTRUCTIVE_ACTIONS", "true").lower() == "true"
    privacy_mode: bool = os.getenv("PRIVACY_MODE", "false").lower() == "true"

@dataclass
class DatabaseConfig:
    db_type: str = os.getenv("DATABASE_TYPE", os.getenv("DB_TYPE", "mongodb" if os.getenv("MONGODB_URI") else ("postgres" if os.getenv("POSTGRES_URL") or os.getenv("POSTGRES_PASSWORD") else "sqlite")))
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db: str = os.getenv("MONGODB_DB", "ajax_ai")
    postgres_url: str = os.getenv("POSTGRES_URL", "")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db: str = os.getenv("POSTGRES_DB", "ajax_ai")

@dataclass
class MeiliSearchConfig:
    host: str = os.getenv("MEILISEARCH_HOST", "http://127.0.0.1:7700")
    key: str = os.getenv("MEILISEARCH_KEY", "")
    index: str = os.getenv("MEILISEARCH_INDEX", "ajax_graphrag")

@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    meilisearch: MeiliSearchConfig = field(default_factory=MeiliSearchConfig)
    database_path: str = os.getenv("DATABASE_PATH", os.path.join(DATA_DIR, "ajax.db"))
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    api_docs_enabled: bool = os.getenv(
        "API_DOCS_ENABLED",
        "true" if os.getenv("DEBUG", "false").lower() == "true" else "false"
    ).lower() == "true"
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
    allow_sqlite_fallback: bool = os.getenv(
        "ALLOW_SQLITE_FALLBACK",
        "false" if os.getenv("VERCEL") else "true"
    ).lower() == "true"
    cloud_name: str = os.getenv("CLOUD_NAME", "")
    cloud_api_key: str = os.getenv("CLOUD_API_KEY", "")
    cloud_api_secret: str = os.getenv("CLOUD_API_SECRET", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    demo_login_enabled: bool = os.getenv("DEMO_LOGIN_ENABLED", "false").lower() == "true"
    demo_username: str = os.getenv("DEMO_USERNAME", "demo")
    demo_password: str = os.getenv("DEMO_PASSWORD", "")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
    rag_embedding_provider: str = os.getenv("RAG_EMBEDDING_PROVIDER", "auto")
    rag_embedding_model: str = os.getenv(
        "RAG_EMBEDDING_MODEL",
        "paraphrase-multilingual-MiniLM-L12-v2"
    )
    auto_training_enabled: bool = os.getenv("AUTO_TRAINING_ENABLED", "true").lower() == "true"
    auto_training_min_new_samples: int = max(1, int(os.getenv("AUTO_TRAINING_MIN_NEW_SAMPLES", "10")))
    auto_training_check_interval_seconds: int = max(30, int(os.getenv("AUTO_TRAINING_CHECK_INTERVAL_SECONDS", "300")))
    auto_training_cooldown_seconds: int = max(300, int(os.getenv("AUTO_TRAINING_COOLDOWN_SECONDS", "1800")))
    auto_training_initial_delay_seconds: int = max(5, int(os.getenv("AUTO_TRAINING_INITIAL_DELAY_SECONDS", "30")))

    def _safe_settings_payload(self) -> Dict[str, Any]:
        """Return only non-secret settings suitable for persistence."""
        return {
            "llm": {
                key: getattr(self.llm, key)
                for key in PERSISTED_LLM_FIELDS
                if hasattr(self.llm, key)
            },
            "voice": asdict(self.voice),
            "safety": asdict(self.safety),
        }

    def save_to_file(self):
        payload = self._safe_settings_payload()
        try:
            from database.db import is_mongo_active, get_mongo_db
            if is_mongo_active():
                db = get_mongo_db()
                db.system_settings.update_one({"id": "app_config"}, {"$set": payload}, upsert=True)
        except Exception:
            pass

        try:
            temp_file = f"{SETTINGS_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            os.replace(temp_file, SETTINGS_FILE)
        except Exception as e:
            pass

    @classmethod
    def load(cls) -> "AppConfig":
        config = cls()
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "llm" in data:
                        for k in PERSISTED_LLM_FIELDS:
                            if k in data["llm"] and hasattr(config.llm, k):
                                setattr(config.llm, k, data["llm"][k])
                        # Migrate old local-daemon settings to AJAX's own
                        # native engine. No Ollama model is started anymore.
                        if str(config.llm.provider).strip().lower() in {"ollama", "qwen3.5:4b"}:
                            config.llm.provider = "ajax_local"
                            config.llm.model = "ajax-native-100-intents"
                        # Never re-enable hidden chain-of-thought output from a
                        # stale settings file.
                        config.llm.thinking_mode = False
                    if "voice" in data:
                        for k, v in data["voice"].items():
                            if hasattr(config.voice, k):
                                setattr(config.voice, k, v)
                    if "safety" in data:
                        for k, v in data["safety"].items():
                            if hasattr(config.safety, k):
                                setattr(config.safety, k, v)

                    # Scrub legacy settings files that may have stored secrets
                    # before the allowlisted persistence format was introduced.
                    legacy_secret_keys = {
                        "api_key", "groq_api_key", "gemini_api_key",
                        "deepseek_api_key", "openrouter_api_key",
                        "database", "cloud_api_secret", "jwt_secret",
                        "admin_password", "demo_password"
                    }
                    has_legacy_secrets = bool(
                        legacy_secret_keys.intersection(data.keys())
                        or legacy_secret_keys.intersection(data.get("llm", {}).keys())
                    )
                    if has_legacy_secrets:
                        temp_file = f"{SETTINGS_FILE}.tmp"
                        with open(temp_file, "w", encoding="utf-8") as safe_file:
                            json.dump(config._safe_settings_payload(), safe_file, indent=4)
                        os.replace(temp_file, SETTINGS_FILE)
            except Exception as e:
                print(f"Error loading custom settings: {e}")
        # AJAX runs on its local engines only. Ignore stale or externally
        # configured cloud providers so the settings surface stays clear and
        # no cloud credential can silently become the active provider.
        if str(config.llm.provider).strip().lower() not in {"ajax_local", "ajax_gguf"}:
            config.llm.provider = "ajax_local"
            config.llm.model = "ajax-native-100-intents"
        return config

# Global config instance
config = AppConfig.load()
