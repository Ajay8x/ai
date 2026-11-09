"""Regression coverage for the merged intent catalog and routing boundaries."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.neural.dataset_loader import INTENT_MERGE_MAP, load_intent_dataset
from ai.neural.intent_classifier import intent_classifier


class TestIntentMerge(unittest.TestCase):
    def test_catalog_is_merged_and_checkpoint_labels_match(self):
        data = load_intent_dataset("data/intents.json")
        labels = {item["intent"] for item in data["intents"]}

        self.assertEqual(len(labels), 92)
        self.assertEqual(intent_classifier.num_classes, len(labels))
        self.assertEqual(set(intent_classifier.intent_labels), labels)
        self.assertTrue(INTENT_MERGE_MAP)
        self.assertIn("TEXT_EDITING", labels)
        self.assertIn("TASK_PLANNING", labels)
        self.assertIn("EMAIL_ASSIST", labels)
        self.assertNotIn("DEFINE_TERM", labels)
        self.assertNotIn("EMAIL_SUMMARY", labels)

    def test_specialized_boundaries_win_over_broad_guards(self):
        cases = {
            "open youtube": "OPEN_WEBSITE",
            "show me what you remember about me": "MEMORY_RECALL",
            "create a QR code please": "QR_CODE",
            "calculate body mass index from height and weight": "BMI_CALCULATION",
            "what tip should I leave on a restaurant bill": "TIP_CALCULATION",
            "fix the layout of my web page using HTML and CSS": "HTML_CSS_HELP",
            "write pytest tests for this code": "TEST_GENERATION",
            "check whether my internet connection is working": "NETWORK_TEST",
        }

        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(intent_classifier.predict(query)["intent"], expected)

    def test_each_active_intent_has_a_representative_pattern(self):
        data = load_intent_dataset("data/intents.json")
        self.assertEqual(len(data["intents"]), 92)
        self.assertTrue(all(item.get("patterns") for item in data["intents"]))


if __name__ == "__main__":
    unittest.main()
