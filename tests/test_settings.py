"""Regression checks for the authenticated settings surface."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from controllers.system_controller import SettingsUpdateRequest, get_settings


class TestSettings(unittest.TestCase):
    def test_authenticated_settings_report_runtime_neural_counts(self):
        payload = get_settings({"id": "user-123", "role": "user"})

        self.assertEqual(payload["neural"]["num_classes"], payload["neural"]["intents_dataset_count"])
        self.assertEqual(payload["neural"]["num_classes"], 92)
        self.assertEqual(payload["llm"]["thinking_mode"], False)
        self.assertNotIn("gemini_key_masked", payload["llm"])

    def test_settings_page_uses_correct_safe_defaults(self):
        project_root = Path(__file__).resolve().parents[1]
        page = (project_root / "views" / "templates" / "pages" / "settings.html").read_text(encoding="utf-8")

        self.assertIn("id=\"telemetryClasses\">Loading...", page)
        self.assertIn("id=\"telemetryVocab\">Loading...", page)
        self.assertIn("data.llm.provider || 'ajax_local'", page)
        self.assertIn("settingsIsAdmin", page)
        self.assertNotIn('value="gemini"', page)
        self.assertNotIn('id="keyGemini"', page)
        self.assertNotIn('id="keyGroq"', page)
        self.assertNotIn('id="keyOpenAI"', page)

    def test_chat_page_uses_single_local_gguf_model(self):
        project_root = Path(__file__).resolve().parents[1]
        page = (project_root / "views" / "templates" / "pages" / "chat.html").read_text(encoding="utf-8")

        self.assertIn("AJAX Chat Core · GGUF 1.7B", page)
        self.assertIn('class="chat-model-fixed"', page)
        self.assertNotIn('id="chatModelSelector"', page)
        self.assertNotIn('ajax_safetensors', page)
        self.assertIn("Router ON", page)

    def test_chat_session_switch_loads_persisted_messages(self):
        project_root = Path(__file__).resolve().parents[1]
        page = (project_root / "views" / "templates" / "pages" / "chat.html").read_text(encoding="utf-8")

        self.assertIn("async function loadConversationHistory(convId)", page)
        self.assertIn("/api/conversations/${encodeURIComponent(convId)}", page)
        self.assertIn("await loadConversationHistory(convId)", page)

    def test_brain_topology_contains_current_model_nodes(self):
        project_root = Path(__file__).resolve().parents[1]
        page = (project_root / "views" / "templates" / "pages" / "brain.html").read_text(encoding="utf-8")

        self.assertIn("AJAX Neural Router · ONNX/PT", page)
        self.assertIn("ONNX Intent Runtime", page)
        self.assertIn("PyTorch .pt Fallback", page)
        self.assertIn("AJAX Chat Core · GGUF 1.7B", page)
        self.assertNotIn("AJAX Chat Lite · Qwen 0.5B", page)
        self.assertIn("async function loadBrainDiagnostics()", page)

    def test_settings_api_accepts_only_ajax_local_providers(self):
        self.assertEqual(SettingsUpdateRequest(llm_provider="ajax_local").llm_provider, "ajax_local")
        with self.assertRaises(ValidationError):
            SettingsUpdateRequest(llm_provider="gemini")


if __name__ == "__main__":
    unittest.main()
