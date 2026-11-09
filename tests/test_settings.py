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

    def test_settings_api_accepts_only_ajax_local_providers(self):
        self.assertEqual(SettingsUpdateRequest(llm_provider="ajax_local").llm_provider, "ajax_local")
        with self.assertRaises(ValidationError):
            SettingsUpdateRequest(llm_provider="gemini")


if __name__ == "__main__":
    unittest.main()
