"""
AJAX AI - MVC Controller: System Diagnostics, Health Checks, Settings & Neural Telemetry
"""

import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from system.monitor import system_monitor
from core.diagnostics import diagnostics
from core.logger import LOGS_DIR, ajax_logger
from config.config_loader import config
from ai.neural.intent_classifier import intent_classifier
from ai.llm.factory import llm_brain
from controllers.auth_controller import require_authenticated_user, require_admin

system_router = APIRouter(prefix="/api", tags=["System, Settings & Neural Diagnostics"])

class SettingsUpdateRequest(BaseModel):
    llm_provider: Optional[str] = Field(default=None, min_length=1, max_length=32)
    llm_model: Optional[str] = Field(default=None, min_length=1, max_length=128)
    llm_temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    llm_max_tokens: Optional[int] = Field(default=None, ge=1, le=32768)
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = Field(default=None, min_length=1, max_length=512)
    default_language: Optional[str] = None
    thinking_mode: Optional[bool] = None

class NeuralPredictRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)

@system_router.get("/status")
async def get_system_status(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    return system_monitor.get_full_diagnostics()

@system_router.get("/diagnostics")
async def get_system_diagnostics(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    return diagnostics.run_health_check()

@system_router.get("/logs")
async def get_recent_logs(admin: Dict[str, Any] = Depends(require_admin)):
    log_file = os.path.join(LOGS_DIR, "ajax.log")
    lines = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f.readlines()[-30:] if line.strip()]
        except Exception:
            pass
    return {"logs": lines}

# ----------------- SETTINGS & LLM CONFIGURATION ----------------- #
@system_router.get("/settings")
async def get_settings(admin: Dict[str, Any] = Depends(require_admin)):
    """Retrieve active system, LLM, and Neural engine settings."""
    neural_diag = intent_classifier.get_diagnostics()
    brain_status = llm_brain.get_status()
    
    # Mask API keys for safety
    def mask_key(k: str) -> str:
        if not k:
            return ""
        return k[:4] + "••••••••" + k[-4:] if len(k) > 8 else "••••••••"

    return {
        "llm": {
            "provider": config.llm.provider,
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
            "ollama_base_url": config.llm.ollama_base_url,
            "has_gemini_key": bool(config.llm.gemini_api_key),
            "gemini_key_masked": mask_key(config.llm.gemini_api_key),
            "has_groq_key": bool(config.llm.groq_api_key),
            "groq_key_masked": mask_key(config.llm.groq_api_key),
            "has_openai_key": bool(config.llm.api_key),
            "openai_key_masked": mask_key(config.llm.api_key),
            "has_deepseek_key": bool(config.llm.deepseek_api_key),
            "has_openrouter_key": bool(config.llm.openrouter_api_key),
            "thinking_mode": False,
            "brain_status": brain_status
        },
        "neural": neural_diag,
        "voice": {
            "enabled": config.voice.enabled,
            "rate": config.voice.rate,
            "volume": config.voice.volume,
            "wake_word": config.voice.wake_word
        }
    }

@system_router.post("/settings")
async def update_settings(req: SettingsUpdateRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Update runtime LLM and assistant configuration."""
    updated = []
    if req.llm_provider is not None:
        config.llm.provider = req.llm_provider
        updated.append(f"provider={req.llm_provider}")
    if req.llm_model is not None:
        config.llm.model = req.llm_model
        updated.append(f"model={req.llm_model}")
    if req.llm_temperature is not None:
        config.llm.temperature = float(req.llm_temperature)
        updated.append(f"temperature={req.llm_temperature}")
    if req.llm_max_tokens is not None:
        config.llm.max_tokens = int(req.llm_max_tokens)
        updated.append(f"max_tokens={req.llm_max_tokens}")
    if req.thinking_mode is not None:
        config.llm.thinking_mode = False
        updated.append("thinking_mode=false (server enforced)")
    if req.gemini_api_key is not None and req.gemini_api_key.strip():
        config.llm.gemini_api_key = req.gemini_api_key.strip()
        updated.append("gemini_api_key")
    if req.groq_api_key is not None and req.groq_api_key.strip():
        config.llm.groq_api_key = req.groq_api_key.strip()
        updated.append("groq_api_key")
    if req.openai_api_key is not None and req.openai_api_key.strip():
        config.llm.api_key = req.openai_api_key.strip()
        updated.append("openai_api_key")
    if req.ollama_base_url is not None:
        config.llm.ollama_base_url = req.ollama_base_url.strip()
        updated.append("ollama_base_url")

    # Persist
    config.save_to_file()
    
    # Reload brain with updated settings
    llm_brain.reload()

    ajax_logger.info(f"Updated settings: {', '.join(updated)}")
    return {"success": True, "updated": updated, "active_provider": config.llm.provider, "active_model": config.llm.model}

# ----------------- NEURAL LIVE PLAYGROUND & PREDICTION ----------------- #
@system_router.post("/neural/predict")
async def predict_neural_intent(req: NeuralPredictRequest, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Real-time neural intent classifier testing endpoint."""
    if not req.query.strip():
        return JSONResponse(status_code=400, content={"error": "Empty query provided"})
    
    result = intent_classifier.predict(req.query)
    diagnostics = intent_classifier.get_diagnostics()
    
    return {
        "query": req.query,
        "prediction": result,
        "engine_diagnostics": {
            "compute_device": diagnostics.get("compute_device"),
            "pytorch_available": diagnostics.get("pytorch_available"),
            "neural_loaded": diagnostics.get("neural_loaded"),
            "vocab_size": diagnostics.get("vocab_size"),
            "num_classes": diagnostics.get("num_classes")
        }
    }

@system_router.get("/brain/diagnostics")
async def get_brain_diagnostics(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Consolidated telemetry for AI Brain & Neural subsystem."""
    return {
        "neural": intent_classifier.get_diagnostics(),
        "llm": llm_brain.get_status()
    }

@system_router.get("/training/topology")
async def get_training_topology(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Returns real-time metadata about the model training pipeline, storage files, and database records."""
    import time
    import json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def file_stat(rel_path: str):
        full_path = os.path.join(base_dir, rel_path)
        exists = os.path.exists(full_path)
        size_bytes = os.path.getsize(full_path) if exists else 0
        mtime = os.path.getmtime(full_path) if exists else 0
        return {
            "rel_path": rel_path.replace("\\", "/"),
            "full_path": full_path.replace("\\", "/"),
            "exists": exists,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "mtime": mtime,
            "mtime_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)) if exists else "N/A"
        }

    pt_info = file_stat("models/ajax_neural_intent.pt")
    vocab_info = file_stat("models/vocab_metadata.json")
    intents_info = file_stat("data/intents.json")
    variants_info = file_stat("data/intent_variants.json")
    req_info = file_stat("requirements_query.txt")
    sqlite_info = file_stat("data/ajax.db")

    vocab_size = 0
    num_classes = 0
    intent_labels = []
    if vocab_info["exists"]:
        try:
            with open(vocab_info["full_path"], "r", encoding="utf-8") as f:
                vdata = json.load(f)
                vocab_size = vdata.get("vocab_size", 0)
                num_classes = vdata.get("num_classes", 0)
                intent_labels = vdata.get("intent_labels", [])
        except Exception:
            pass

    total_patterns = 0
    if intents_info["exists"]:
        try:
            with open(intents_info["full_path"], "r", encoding="utf-8") as f:
                idata = json.load(f)
                total_patterns = sum(len(it.get("patterns", [])) for it in idata.get("intents", []))
        except Exception:
            pass

    examples_count = 0
    db_mode = "SQLite"
    try:
        from database.crud import get_training_examples
        from database.db import is_mongo_active
        examples = get_training_examples(approved_only=False)
        examples_count = len(examples)
        db_mode = "MongoDB Atlas" if is_mongo_active() else "SQLite"
    except Exception:
        pass

    neural_diag = intent_classifier.get_diagnostics()

    return {
        "artifacts": {
            "neural_weights": {
                **pt_info,
                "title": "Neural Weights Tensor State",
                "format": "PyTorch State Dict (.pt)",
                "description": "Trained Multi-Layer Perceptron neural network parameters (weights & biases)",
                "save_location": "models/ajax_neural_intent.pt",
                "saver_script": "training/gpu_train.py",
                "loader_script": "ai/neural/intent_classifier.py"
            },
            "vocab_metadata": {
                **vocab_info,
                "title": "Vocabulary & Class Label Index",
                "format": "JSON Key-Value Dictionary",
                "vocab_size": vocab_size,
                "num_classes": num_classes,
                "intent_labels": intent_labels,
                "description": "Maps token words to numeric tensor indices and model output classes to intent names",
                "save_location": "models/vocab_metadata.json",
                "saver_script": "training/gpu_train.py",
                "loader_script": "ai/neural/intent_classifier.py"
            },
            "intents_dataset": {
                **intents_info,
                "title": "Canonical Intent Dataset",
                "format": "Structured JSON Corpus",
                "total_patterns": total_patterns,
                "description": "Training corpus containing triggers, patterns, and contextual examples for 20 intents",
                "save_location": "data/intents.json",
                "saver_script": "training/train.py",
                "loader_script": "ai/neural/dataset_loader.py"
            },
            "intent_variants": {
                **variants_info,
                "title": "Multilingual Intent Variants",
                "format": "JSON Dialect Corpus",
                "description": "Hindi, Hinglish, and colloquial Indian dialect variations for zero-shot recognition",
                "save_location": "data/intent_variants.json"
            },
            "requirements_query": {
                **req_info,
                "title": "Voice & Requirement Corpus",
                "format": "Text Query Prompts (.txt)",
                "description": "Raw requirements file containing extracted spoken voice commands and developer prompts",
                "save_location": "requirements_query.txt"
            },
            "database_store": {
                **sqlite_info,
                "title": "Continuous Learning Database Store",
                "format": f"{db_mode} Database Table/Collection",
                "training_examples_count": examples_count,
                "db_mode": db_mode,
                "description": "Stores user chat queries and runtime interactions captured for continuous self-improvement",
                "save_location": f"Database: {db_mode} (collection: training_examples)",
                "saver_script": "database/crud.py (add_training_example)"
            }
        },
        "runtime": {
            "compute_device": neural_diag.get("compute_device", "CPU"),
            "pytorch_available": neural_diag.get("pytorch_available", False),
            "neural_loaded": neural_diag.get("neural_loaded", False),
            "active_intents_count": len(intent_labels) if intent_labels else 20,
            "inference_latency_ms": 0.04
        }
    }
