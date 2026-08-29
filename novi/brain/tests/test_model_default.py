"""Tests for the default chat model (nemotron-3.5-lightning since 2026-08-29).

The fast/natural default: nemotron answers directly in ~1s with think:false,
where qwen3:4b narrated its chain-of-thought into replies. qwen3 tiers stay
switchable. Deterministic, no network.
"""

from __future__ import annotations

import unittest

from novi.brain.models.ollama_reasoning import DEFAULT_OLLAMA_MODEL, OllamaReasoningProvider
from novi.web.server import NoviWebServer


class ModelDefaultTest(unittest.TestCase):
    def test_default_ollama_model_is_nemotron(self) -> None:
        self.assertEqual(DEFAULT_OLLAMA_MODEL, "nemotron-3.5-lightning")

    def test_reasoning_provider_default_model_id(self) -> None:
        provider = OllamaReasoningProvider()
        self.assertIn("nemotron-3.5-lightning", provider.model_id)

    def test_web_server_default_model_is_nemotron(self) -> None:
        server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            self.assertEqual(server.llm_model, "nemotron-3.5-lightning")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
