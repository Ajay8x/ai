"""
AJAX AI - Comprehensive Test Suite
Tests Database CRUD, Tool Registry, Intent Classifier, Safety Engine, and Request Router.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_db_connection
from database.crud import (
    create_conversation,
    add_message,
    save_memory,
    search_memories,
    delete_memory,
    get_conversation_messages,
    list_conversations,
    delete_conversation
)

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

    def test_streaming_router(self):
        conv_id = create_conversation("Stream Test")
        stream_chunks = list(router.process_query_stream("what time is it", conv_id))
        self.assertGreater(len(stream_chunks), 0)
        has_token = any('"type": "token"' in chunk for chunk in stream_chunks)
        has_done = any('"type": "done"' in chunk for chunk in stream_chunks)
        self.assertTrue(has_token)
        self.assertTrue(has_done)

    def test_conversation_history_and_persistence(self):
        conv_id = create_conversation("History Test")
        add_message(conv_id, "user", "Hello assistant")
        add_message(conv_id, "assistant", "Hello! How can I help?")
        
        msgs = get_conversation_messages(conv_id)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["content"], "Hello assistant")
        
        from database.crud import list_conversations, delete_conversation
        convs = list_conversations()
        self.assertTrue(any(c["id"] == conv_id for c in convs))
        
        deleted = delete_conversation(conv_id)
        self.assertTrue(deleted)

    def test_coding_intent_and_generation(self):
        # Disambiguate 'hello world' in code query from pure greeting
        pred = intent_classifier.predict("give me simple code java hello world")
        self.assertEqual(pred["intent"], "WRITE_CODE")
        self.assertIsNone(pred.get("predefined_response"))

        # Pure greeting must still predict GREETING
        greet_pred = intent_classifier.predict("hello")
        self.assertEqual(greet_pred["intent"], "GREETING")
        self.assertIsNotNone(greet_pred.get("predefined_response"))

        # Router must generate Java Hello World code
        conv_id = create_conversation("Code Test")
        res = router.process_query("give me simple code java hello world", conv_id)
        self.assertEqual(res["intent"], "WRITE_CODE")
        self.assertIn("HelloWorld", res["response"])
        self.assertIn("System.out.println", res["response"])
        delete_conversation(conv_id)

    def test_math_calculation_and_plugins(self):
        # Math intent and tool execution
        pred = intent_classifier.predict("calculate square root of 144")
        self.assertEqual(pred["intent"], "CALCULATE")
        self.assertEqual(pred["tool"], "calculate")

        conv_id = create_conversation("Math Test")
        res = router.process_query("calculate square root of 144", conv_id)
        self.assertEqual(res["intent"], "CALCULATE")
        self.assertIn("12", res["response"])
        delete_conversation(conv_id)

        # Plugins discovery
        from plugins.manager import plugin_manager
        plugins = plugin_manager.list_plugins()
        self.assertGreaterEqual(len(plugins), 3)
        plugin_names = [p["name"] for p in plugins]
        self.assertIn("ScientificCalculator", plugin_names)
        self.assertIn("ProductivitySuite", plugin_names)
        self.assertIn("WeatherIntelligence", plugin_names)

if __name__ == "__main__":
    unittest.main()

