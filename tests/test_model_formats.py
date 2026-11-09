"""Regression checks for local GGUF chat and ONNX intent support."""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.neural.intent_classifier import intent_classifier
from controllers.system_controller import SettingsUpdateRequest


class TestModelFormats(unittest.TestCase):
    def test_onnx_artifact_matches_runtime_metadata(self):
        model_path = Path("models/ajax_neural_intent.onnx")
        metadata_path = Path("models/vocab_metadata.json")
        self.assertTrue(model_path.exists())
        self.assertTrue(metadata_path.exists())

        import onnx

        with metadata_path.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)
        graph = onnx.load(str(model_path)).graph
        input_shape = graph.input[0].type.tensor_type.shape.dim
        output_shape = graph.output[0].type.tensor_type.shape.dim
        self.assertEqual(input_shape[-1].dim_value, metadata["vocab_size"])
        self.assertEqual(output_shape[-1].dim_value, metadata["num_classes"])

    def test_classifier_uses_a_supported_neural_backend(self):
        diagnostics = intent_classifier.get_diagnostics()
        self.assertIn(diagnostics["inference_backend"], {"onnx", "pytorch"})
        self.assertEqual(intent_classifier.predict("what is the time right now")["intent"], "TIME")
        self.assertEqual(intent_classifier.predict("check whether my internet connection is working")["intent"], "NETWORK_TEST")

    def test_settings_keep_gguf_chat_and_onnx_intent_options(self):
        self.assertEqual(
            SettingsUpdateRequest(llm_provider="ajax_gguf").llm_provider,
            "ajax_gguf",
        )
        request = SettingsUpdateRequest(
            neural_backend="onnx",
            onnx_model_path="models/ajax_neural_intent.onnx",
        )
        self.assertEqual(request.neural_backend, "onnx")

        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            SettingsUpdateRequest(llm_provider="ajax_safetensors")


if __name__ == "__main__":
    unittest.main()
