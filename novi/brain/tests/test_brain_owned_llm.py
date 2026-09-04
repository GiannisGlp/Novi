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
import unittest
from unittest import mock

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


def _resp(payload: object, status: int = 200):
    resp = mock.MagicMock()
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    resp.status = status
    resp.__enter__.return_value = resp
    return resp


class _FakeOllama:
    """Socket-free stand-in for Ollama's /api/tags and /api/chat endpoints.

    Patches ``urllib.request.urlopen`` (repo convention: unit tests run
    anywhere with no server and no sockets — cf. test_chat_server.py).
    """

    def __init__(self, reply: str = "I stored that near your desk notes.") -> None:
        self.reply = reply
        self.received: list[dict] = []
        self._patcher: mock._patch | None = None

    def start(self) -> str:
        outer = self

        def _fake_urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if url.endswith("/api/tags"):
                return _resp({"models": [{"name": "brain-default"}]})
            outer.received.append(json.loads(req.data.decode("utf-8")))
            return _resp({"message": {"role": "assistant", "content": outer.reply}})

        self._patcher = mock.patch("urllib.request.urlopen", side_effect=_fake_urlopen)
        self._patcher.start()
        return "http://fake-ollama"

    def stop(self) -> None:
        if self._patcher is not None:
            self._patcher.stop()
            self._patcher = None


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
        import urllib.error

        # The setUp fake patches urlopen globally: stop it so this endpoint
        # is genuinely unreachable, and fail fast without real sockets.
        self.fake.stop()
        cfg = MacBrainConfig(
            curiosity_enabled=False,
            brain_llm_enabled=True,
            brain_llm_url="http://127.0.0.1:1",  # nothing listens here
        )
        brain = _brain(config=cfg)
        brain.start()
        try:
            with mock.patch(
                "urllib.request.urlopen",
                side_effect=urllib.error.URLError("nothing listens here"),
            ):
                resp = brain.respond("anything at all")
            # Model unreachable -> the brain degrades to the deterministic
            # fallback (never raises, never fabricates).
            self.assertNotEqual(resp.get("reply_source"), "dialogue")
            self.assertTrue(resp["text"])
        finally:
            brain.stop()


class BrainLLMServerDialectTests(unittest.TestCase):
    """The brain-owned transport speaks the configured server dialect.

    ``brain_llm_server="ollama"`` (default) keeps the native /api/chat wire
    format; ``"openai-compatible"`` speaks /v1 so llama.cpp/vLLM frontends
    are drop-in backends. HTTP is mocked: these run anywhere.
    """

    def _brain(self, **cfg_kw) -> MacBrain:
        cfg = MacBrainConfig(curiosity_enabled=False, brain_llm_enabled=True, **cfg_kw)
        return _brain(config=cfg)

    def test_generic_dialect_posts_v1_chat(self) -> None:
        from unittest import mock as _mock

        from novi.brain.models.chat_server import OpenAICompatibleChatServer

        seen: dict[str, object] = {}

        class _FakeServer(OpenAICompatibleChatServer):
            def chat(self, **kw):  # type: ignore[override]
                seen.update(kw)
                return "generic hello"

        brain = self._brain(
            brain_llm_server="openai-compatible", brain_llm_model="qwen3:8b"
        )
        with _mock.patch(
            "novi.brain.models.chat_server.OpenAICompatibleChatServer", return_value=_FakeServer("http://x")
        ):
            reply = brain._brain_llm_call(system="s", user="hi")
        self.assertEqual(reply, "generic hello")
        self.assertEqual(seen.get("model"), "qwen3:8b")

    def test_ollama_dialect_unchanged(self) -> None:
        import json as _json
        from unittest import mock as _mock

        def _resp(payload: object):
            resp = _mock.MagicMock()
            resp.read.return_value = _json.dumps(payload).encode("utf-8")
            resp.__enter__.return_value = resp
            return resp

        brain = self._brain(brain_llm_model="qwen3:8b")
        with _mock.patch(
            "urllib.request.urlopen",
            return_value=_resp({"message": {"content": "ollama hello"}}),
        ) as opened:
            reply = brain._brain_llm_call(system="s", user="hi")
        self.assertEqual(reply, "ollama hello")
        self.assertTrue(opened.call_args.args[0].full_url.endswith("/api/chat"))

    def test_generic_probe_uses_v1_models(self) -> None:
        import json as _json
        from unittest import mock as _mock

        def _resp(payload: object):
            resp = _mock.MagicMock()
            resp.read.return_value = _json.dumps(payload).encode("utf-8")
            resp.__enter__.return_value = resp
            return resp

        brain = self._brain(
            brain_llm_server="openai-compatible", brain_llm_model="qwen3:8b"
        )
        with _mock.patch(
            "urllib.request.urlopen",
            return_value=_resp({"data": [{"id": "qwen3:8b"}]}),
        ) as opened:
            self.assertTrue(brain._brain_llm_reachable())
        self.assertTrue(opened.call_args.args[0].full_url.endswith("/v1/models"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
