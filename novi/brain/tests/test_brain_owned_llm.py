"""Phase 3e (north-star gap analysis): the brain owns its default LLM transport.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 3e:
"Move a default LLM provider inside MacBrain so surfaces pass only the
message and the brain owns the reply regardless of source. Surfaces may
still override for model tiering."

Acceptance:
- brain.respond(text) produces a grounded LLM reply with NO transport
  argument when the brain's default transport is enabled;
- a surface that injects nothing still gets the brain's default provider;
- the no-assistant/no-repetition guardrails still apply to brain-default
  replies;
- with the default disabled (CI default), behavior is unchanged (text=None
  fallback paths).
"""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


class _Cam:
    def __init__(self) -> None:
        self.sequence = 0

    def close(self) -> None:
        self.sequence = self.sequence

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"f-{self.sequence}",
            captured_at="2026-08-29T12:00:00Z",
            width=2,
            height=2,
            payload=b"frame",
            metadata={"backend": "test"},
        )


def _brain(config: MacBrainConfig | None = None, llm_chat=None) -> MacBrain:
    return MacBrain(
        camera=_Cam(),
        perception=SpecialistPerception(),
        llm_chat=llm_chat,
        config=config or MacBrainConfig(curiosity_enabled=False),
    )


class _FakeOllama:
    """Minimal stand-in for Ollama's /api/chat and /api/tags endpoints."""

    def __init__(self, reply: str = "I stored that near your desk notes.") -> None:
        self.reply = reply
        self.received: list[dict] = []
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                body = json.dumps({"models": [{"name": "brain-default"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):  # noqa: N802
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                outer.received.append(payload)
                body = json.dumps({"message": {"role": "assistant", "content": outer.reply}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):  # silence test output
                return

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return f"http://127.0.0.1:{port}"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()


class BrainOwnedTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = _FakeOllama()
        self.url = self.fake.start()

    def tearDown(self) -> None:
        self.fake.stop()

    def _config(self) -> MacBrainConfig:
        return MacBrainConfig(
            curiosity_enabled=False,
            brain_llm_enabled=True,
            brain_llm_url=self.url,
            brain_llm_model="brain-owned-model",
        )

    def test_respond_without_transport_argument_uses_brain_default(self):
        brain = _brain(config=self._config())
        brain.start()
        try:
            resp = brain.respond("remember the cup is on the desk")
            self.assertTrue(resp["text"], "the brain must own the reply with no injected transport")
            self.assertIn("stored", resp["text"])
            self.assertEqual(resp["reply_source"], "dialogue")
            self.assertEqual(len(self.fake.received), 1, "exactly one brain-owned model call")
            self.assertEqual(self.fake.received[0]["model"], "brain-owned-model")
        finally:
            brain.stop()

    def test_guardrails_apply_to_brain_default_replies(self):
        self.fake.reply = "Sure! How can I help you today?"
        brain = _brain(config=self._config())
        brain.start()
        try:
            resp = brain.respond("what's the weather on mars")
            self.assertNotIn("how can i help", (resp["text"] or "").lower())
        finally:
            brain.stop()

    def test_override_still_wins_for_model_tiering(self):
        calls: list[str] = []

        def override(*, system: str, user: str, temperature: float = 0.5, timeout: int = 120):
            calls.append(user)
            return "override reply"

        brain = _brain(config=self._config(), llm_chat=override)
        brain.start()
        try:
            resp = brain.respond("remember the cup is on the desk")
            self.assertEqual(resp["text"], "override reply")
            self.assertEqual(self.fake.received, [], "the override must bypass the brain default")
        finally:
            brain.stop()

    def test_disabled_default_keeps_ci_contract(self):
        brain = _brain(config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        try:
            self.assertIsNone(brain.default_llm_chat())
            # respond() still answers via the deterministic banks (its own
            # documented fallback contract), but never through a model.
            resp = brain.respond("plain statement")
            self.assertEqual(resp["reply_source"], "fallback")
        finally:
            brain.stop()

    def test_unreachable_endpoint_degrades_without_raising(self):
        cfg = MacBrainConfig(
            curiosity_enabled=False,
            brain_llm_enabled=True,
            brain_llm_url="http://127.0.0.1:1",  # nothing listens here
        )
        brain = _brain(config=cfg)
        brain.start()
        try:
            resp = brain.respond("anything at all")
            # Model unreachable -> the brain degrades to the deterministic
            # fallback (never raises, never fabricates).
            self.assertNotEqual(resp.get("reply_source"), "dialogue")
            self.assertTrue(resp["text"])
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
