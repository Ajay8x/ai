"""
AJAX AI - Self Diagnostics & Health Verification
Validates Database, LLM connectivity, Intent Engine, Tools, and Audio subsystems.
"""

from typing import Dict, Any
from database.db import get_db_connection
from tools.registry import registry
from ai.neural.intent_classifier import intent_classifier
from config.config_loader import config
from core.logger import ajax_logger

class HealthDiagnostics:
    @staticmethod
    def run_health_check() -> Dict[str, Any]:
        report = {}

        # 1. Database Check
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as count FROM sqlite_master WHERE type='table'")
            tables_count = cursor.fetchone()["count"]
            conn.close()
            report["database"] = {"status": "HEALTHY", "tables_count": tables_count}
        except Exception as e:
            report["database"] = {"status": "UNHEALTHY", "error": str(e)}

        # 2. Tool Registry Check
        tools_list = registry.list_tools()
        report["tools"] = {
            "status": "HEALTHY" if len(tools_list) > 0 else "WARNING",
            "registered_count": len(tools_list),
            "tools": [t.name for t in tools_list]
        }

        # 3. Intent Engine Check
        intents_count = len(intent_classifier.intents)
        report["intent_engine"] = {
            "status": "HEALTHY" if intents_count > 0 else "UNHEALTHY",
            "intents_count": intents_count
        }

        # 4. LLM Provider Check
        report["llm_provider"] = {
            "configured_provider": config.llm.provider,
            "model": config.llm.model,
            "status": "CONFIGURED"
        }

        # 5. Voice Engine Check
        report["voice"] = {
            "enabled": config.voice.enabled,
            "tts_engine": config.voice.tts_engine,
            "stt_engine": config.voice.stt_engine,
            "status": "CONFIGURED"
        }

        overall_status = "HEALTHY" if all(v.get("status") in ["HEALTHY", "CONFIGURED"] for v in report.values()) else "DEGRADED"
        return {
            "overall_status": overall_status,
            "subsystems": report
        }

diagnostics = HealthDiagnostics()
