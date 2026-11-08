"""Regression tests for chat-scoped document retrieval."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context import context_manager
from ai.rag.store import RAGStore, tokenize
from ai.llm.factory import LocalRuleBasedFallbackProvider


class TestChatRAGUpload(unittest.TestCase):
    @patch("core.context.rag_store")
    def test_context_includes_cited_user_scoped_document_chunks(self, mock_rag_store):
        mock_rag_store.query.return_value = [
            {
                "citation": "Project Notes - notes.txt, chunk 1/1",
                "chunk": "The launch checklist owner is Ajay.",
            }
        ]

        messages = context_manager.build_context(
            conversation_id="rag-test-conversation",
            current_query="Who owns the launch checklist?",
            user_id="user-123",
        )

        mock_rag_store.query.assert_called_once_with(
            "Who owns the launch checklist?",
            top_k=4,
            user_id="user-123",
        )
        system_prompt = messages[0]["content"]
        self.assertIn("Project Notes - notes.txt, chunk 1/1", system_prompt)
        self.assertIn("The launch checklist owner is Ajay.", system_prompt)
        self.assertIn("bracketed source citation", system_prompt)

    @patch("core.context.rag_store")
    def test_retrieval_failure_does_not_break_chat_context(self, mock_rag_store):
        mock_rag_store.query.side_effect = RuntimeError("index unavailable")

        messages = context_manager.build_context(
            conversation_id="rag-test-conversation",
            current_query="Tell me about the uploaded document",
            user_id="user-123",
        )

        self.assertTrue(messages)
        self.assertEqual(messages[0]["role"], "system")
        self.assertNotIn("--- RETRIEVED USER DOCUMENTS ---", messages[0]["content"])

    def test_rag_query_keeps_other_users_documents_out_of_results(self):
        store = RAGStore()
        store._initialized = True

        def document(user_id, file_name, chunk):
            return {
                "id": file_name,
                "user_id": user_id,
                "source": file_name,
                "file_name": file_name,
                "title": file_name,
                "chunk": chunk,
                "chunk_index": 0,
                "total_chunks": 1,
                "tokens": set(tokenize(chunk)),
                "embedding": store.embedding_provider.embed(chunk),
            }

        store.documents = [
            document("user-123", "private-a.txt", "Aurora checklist owner is Ajay."),
            document("user-456", "private-b.txt", "Aurora checklist owner is someone else."),
        ]

        results = store.query("Aurora checklist owner", top_k=5, user_id="user-123")

        self.assertTrue(any(item["file_name"] == "private-a.txt" for item in results))
        self.assertFalse(any(item["file_name"] == "private-b.txt" for item in results))

    def test_offline_chat_fallback_uses_retrieved_document_context(self):
        response = LocalRuleBasedFallbackProvider().generate([
            {
                "role": "system",
                "content": "--- RETRIEVED USER DOCUMENTS ---\n[1] notes.txt, chunk 1/1\nThe launch owner is Ajay.\n--- TARGET RESPONSE LANGUAGE ---",
            },
            {"role": "user", "content": "Who owns the launch?"},
        ])

        self.assertIn("The launch owner is Ajay.", response.content)


if __name__ == "__main__":
    unittest.main()
