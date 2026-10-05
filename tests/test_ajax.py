"""
AJAX AI - Comprehensive Test Suite
Tests Database CRUD, Tool Registry, Intent Classifier, Safety Engine, and Request Router.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_db_connection
from database.crud import create_conversation, add_message, save_memory, search_memories, delete_memory
from tools.registry import registry
from ai.neural.intent_classifier import intent_classifier
from core.safety import safety_engine
from core.permissions import PermissionLevel
from core.router import router

class TestAJAXCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_and_memories(self):
        conv_id = create_conversation("Test Unit Conv")
        self.assertTrue(len(conv_id) > 0)
        
        msg_id = add_message(conv_id, "user", "Unit test message")
        self.assertTrue(len(msg_id) > 0)

        mem_id = save_memory("favorite_food", "Biryani", category="user_preference")
        self.assertTrue(len(mem_id) > 0)

        results = search_memories("Biryani")
        self.assertTrue(any(m["value_text"] == "Biryani" for m in results))

        deleted = delete_memory(mem_id)
        self.assertTrue(deleted)

    def test_tool_registry(self):
        tools = registry.list_tools()
        self.assertGreaterEqual(len(tools), 15)
        
        time_tool = registry.get_tool("get_system_time")
        self.assertIsNotNone(time_tool)
        res = time_tool.execute()
        self.assertTrue(res.success)

    def test_safety_engine(self):
        # Protected system path check
        is_safe, msg = safety_engine.is_path_safe(r"C:\Windows\System32")
        self.assertFalse(is_safe)

        # Safe directory check
        is_safe, msg = safety_engine.is_path_safe(r"data\screenshots")
        self.assertTrue(is_safe)

        # Dangerous command pattern check
        is_safe_cmd, _ = safety_engine.validate_command_safety("del /f /s /q C:\\Windows")
        self.assertFalse(is_safe_cmd)

    def test_intent_engine(self):
        res = intent_classifier.predict("what time is it")
        self.assertEqual(res["intent"], "TIME")
        self.assertGreaterEqual(res["confidence"], 0.8)

        res2 = intent_classifier.predict("open chrome")
        self.assertEqual(res2["intent"], "OPEN_APPLICATION")
        self.assertEqual(res2["entities"].get("app_name"), "chrome")

    def test_request_router(self):
        conv_id = create_conversation("Router Test")
        res = router.process_query("what time is it", conv_id)
        self.assertIn("time", res["response"].lower())
        self.assertEqual(res["intent"], "TIME")

if __name__ == "__main__":
    unittest.main()
