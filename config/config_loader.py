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

os.makedirs(DATA_DIR, exist_ok=True)

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
    provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    local_model_path: str = os.getenv("LOCAL_MODEL_PATH", "")

@dataclass
class VoiceConfig:
    enabled: bool = os.getenv("VOICE_ENABLED", "true").lower() == "true"
    wake_word: str = os.getenv("WAKE_WORD", "ajax")
    wake_word_enabled: bool = os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"
    tts_engine: str = os.getenv("TTS_ENGINE", "pyttsx3")
    stt_engine: str = os.getenv("STT_ENGINE", "speech_recognition")
    rate: int = int(os.getenv("VOICE_RATE", "180"))
    volume: float = float(os.getenv("VOICE_VOLUME", "1.0"))

@dataclass
class SafetyConfig:
    level: str = os.getenv("SAFETY_LEVEL", "STANDARD") # STANDARD, STRICT, PERMISSIVE
    require_confirmation: bool = os.getenv("REQUIRE_CONFIRMATION_FOR_DESTRUCTIVE_ACTIONS", "true").lower() == "true"
    privacy_mode: bool = os.getenv("PRIVACY_MODE", "false").lower() == "true"

@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    database_path: str = os.path.join(DATA_DIR, "ajax.db")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    def save_to_file(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    @classmethod
    def load(cls) -> "AppConfig":
        config = cls()
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "llm" in data:
                        for k, v in data["llm"].items():
                            if hasattr(config.llm, k):
                                setattr(config.llm, k, v)
                    if "voice" in data:
                        for k, v in data["voice"].items():
                            if hasattr(config.voice, k):
                                setattr(config.voice, k, v)
                    if "safety" in data:
                        for k, v in data["safety"].items():
                            if hasattr(config.safety, k):
                                setattr(config.safety, k, v)
            except Exception as e:
                print(f"Error loading custom settings: {e}")
        return config

# Global config instance
config = AppConfig.load()
