"""Regression checks for the authenticated settings surface."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.system_controller import get_settings


class TestSettings(unittest.TestCase):
    def test_authenticated_settings_report_runtime_neural_counts(self):
        payload = get_settings({"id": "user-123", "role": "user"})

        self.assertEqual(payload["neural"]["num_classes"], 100)
        self.assertEqual(payload["llm"]["thinking_mode"], False)
        self.assertEqual(payload["llm"]["gemini_key_masked"], "")

    def test_settings_page_uses_correct_safe_defaults(self):
        project_root = Path(__file__).resolve().parents[1]
        page = (project_root / "views" / "templates" / "pages" / "settings.html").read_text(encoding="utf-8")

        self.assertIn("id=\"telemetryClasses\">100 Classes", page)
        self.assertIn("id=\"telemetryVocab\">1020 Words", page)
        self.assertIn("data.llm.provider || 'ajax_local'", page)
        self.assertIn("settingsIsAdmin", page)


if __name__ == "__main__":
    unittest.main()
