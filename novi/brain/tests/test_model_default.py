"""Tests for the default model flip to qwen3:4b (plan 20, O4 / GAP-D).

Deterministic, no network: the DEFAULT_OLLAMA_MODEL constant, the reasoning
provider's model id, and the web server's default llm_model all resolve to
qwen3:4b without an explicit switch.
"""

from __future__ import annotations

import unittest

from novi.brain.models.ollama_reasoning import DEFAULT_OLLAMA_MODEL, OllamaReasoningProvider
from novi.web.server import NoviWebServer


class ModelDefaultTest(unittest.TestCase):
    def test_default_ollama_model_is_qwen3_4b(self) -> None:
        self.assertEqual(DEFAULT_OLLAMA_MODEL, "qwen3:4b")

    def test_reasoning_provider_default_model_id(self) -> None:
        provider = OllamaReasoningProvider()
        self.assertIn("qwen3:4b", provider.model_id)

    def test_web_server_default_model_is_qwen3_4b(self) -> None:
        server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            self.assertEqual(server.llm_model, "qwen3:4b")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
