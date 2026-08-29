"""Tests: LLM payload think-policy + GET /api/health.

The web chat transport must send `think: false` for the fast tiers
(qwen3:4b, qwen3:8b) and omit it for the heavy-thinking tier (qwen3.8:27b),
mirroring the tiering decision. GET /api/health must be reachable for
terminal smoke tests (POST-only was an unhelpful 404 for `curl`).
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from unittest import mock

from novi.web.server import NoviWebHTTPServer, NoviWebServer


def _capture_chat_payload(server: NoviWebServer, model: str, system: str = "s", user: str = "u") -> dict:
    """Call server._llm_chat with a stubbed urlopen; return the sent JSON body."""
    captured: dict = {}

    def fake_open(req, timeout: int = 120):  # noqa: ARG001
        captured["body"] = json.loads(req.data.decode("utf-8"))
        resp = mock.MagicMock()
        resp.read.return_value = json.dumps({"message": {"content": "hi"}}).encode("utf-8")
        resp.__enter__.return_value = resp
        return resp

    server.llm_model = model
    with mock.patch("urllib.request.urlopen", side_effect=fake_open) as stub:
        server._llm_chat(system=system, user=user)
        stub.assert_called_once()
    return captured["body"]


class LLMPayloadThinkTests(unittest.TestCase):
    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def test_fast_tier_sends_think_false_and_small_budget(self) -> None:
        s = self._server()
        try:
            body = _capture_chat_payload(s, "qwen3:4b")
            self.assertIs(body.get("think"), False)
            self.assertEqual(body["options"]["num_predict"], 320)
        finally:
            s.stop()

    def test_heavy_thinking_tier_keeps_thinking_and_gets_budget(self) -> None:
        s = self._server()
        try:
            body = _capture_chat_payload(s, "qwen3.8:27b")
            self.assertNotIn("think", body)
            self.assertEqual(body["options"]["num_predict"], 640)
        finally:
            s.stop()

    def test_build_history_caps_turns_and_text_length(self) -> None:
        s = self._server()
        try:
            s._chat = [{"role": "user", "text": "x" * 500}, {"role": "novi", "text": "y" * 500}] * 8
            history = s._build_history(6)
            self.assertEqual(len(history), 6)
            self.assertTrue(all(len(t["text"]) <= 240 for t in history))
        finally:
            s.stop()


class HealthHttpGetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        cls._server.start()
        cls._httpd = NoviWebHTTPServer(("127.0.0.1", 0), cls._server)
        cls._port = cls._httpd.server_address[1]
        cls._thread = threading.Thread(target=cls._httpd.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._httpd.shutdown()
        cls._httpd.server_close()
        cls._server.stop()

    def test_get_api_health_returns_status(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self._port}/api/health", timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read())
        self.assertIn("status", payload["result"])

    def test_get_recognition_proposals_returns_200(self) -> None:
        """Issue 9: the React Perception page polls this via GET (was 404)."""
        with urllib.request.urlopen(f"http://127.0.0.1:{self._port}/api/recognition/proposals", timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read())
        self.assertIn("proposals", payload["result"])


if __name__ == "__main__":
    unittest.main()
