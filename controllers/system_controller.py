"""
AJAX AI - MVC Controller: System Diagnostics, Health Checks, Settings & Neural Telemetry
"""

import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from system.monitor import system_monitor
from core.diagnostics import diagnostics
from core.logger import LOGS_DIR, ajax_logger
from config.config_loader import config
from ai.neural.intent_classifier import intent_classifier
from ai.llm.factory import llm_brain

system_router = APIRouter(prefix="/api", tags=["System, Settings & Neural Diagnostics"])

class SettingsUpdateRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None
    default_language: Optional[str] = None

class NeuralPredictRequest(BaseModel):
    query: str

@system_router.get("/status")
async def get_system_status():
    return system_monitor.get_full_diagnostics()

@system_router.get("/diagnostics")
async def get_system_diagnostics():
    return diagnostics.run_health_check()

@system_router.get("/logs")
async def get_recent_logs():
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
async def get_settings():
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
async def update_settings(req: SettingsUpdateRequest):
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
async def predict_neural_intent(req: NeuralPredictRequest):
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
async def get_brain_diagnostics():
    """Consolidated telemetry for AI Brain & Neural subsystem."""
    return {
        "neural": intent_classifier.get_diagnostics(),
        "llm": llm_brain.get_status()
    }
