import json
import tempfile
import unittest
from pathlib import Path

from web.server import NoviWebServer


# ═══════════════════════════════════════════════════════════════════
# Shared in-memory server — fast, no durable-store overhead
# ═══════════════════════════════════════════════════════════════════

class NoviWebServerTests(unittest.TestCase):
    """Tests using a shared in-memory server (no SQLite)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._shared = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        cls._shared.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._shared.stop()

    def setUp(self) -> None:
        self.s = self._shared

    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    # ── shared-server tests ──────────────────────────────────────

    def test_state_and_health_serializable(self) -> None:
        st = self.s.state()
        json.dumps(st)
        self.assertIn("cycle", st)
        self.assertIn("health", st)
        self.assertIn(st["health"]["status"], ("PASS", "WARN", "FAIL", "UNKNOWN"))

    def test_hear_accepts_and_returns_serializable(self) -> None:
        r = self.s.hear("alice moved the door")
        json.dumps(r)
        self.assertTrue(r["accepted"])
        self.assertTrue(r["reasoning"])

    def test_audio_event(self) -> None:
        r = self.s.hear_audio(event_hint="alarm", rms=0.7, confidence=0.9)
        json.dumps(r)
        self.assertIn("alarm", [e["event_type"] for e in r["events"]])

    def test_goal_and_step(self) -> None:
        g = self.s.set_goal(x=2.0, y=2.0)
        self.assertEqual(g["kind"], "reach")
        self.assertEqual(g["status"], "active")
        step = self.s.step()
        json.dumps(step)
        self.assertIn("action", step)

    def test_poll_events_increments(self) -> None:
        self.s.hear("alice is here")
        first = self.s.poll_events(0)
        self.assertGreater(len(first["events"]), 0)
        after = first["after"]
        second = self.s.poll_events(after)
        json.dumps(second)
        self.assertGreaterEqual(second["after"], after)

    def test_health(self) -> None:
        h = self.s.health()
        json.dumps(h)
        self.assertIn("status", h)

    def test_clean_chat_text_strips_heard_marker(self) -> None:
        self.assertEqual(self.s._clean_chat_text("[heard] Hello."), "Hello.")
        self.assertEqual(self.s._clean_chat_text("  [heard] hi there"), "hi there")
        self.assertEqual(self.s._clean_chat_text("plain message"), "plain message")

    def test_chat_send_reflects_message(self) -> None:
        r = self.s.chat_send("alice moved the door")
        json.dumps(r)
        self.assertTrue(r["accepted"])
        self.assertEqual(r["novi"]["role"], "novi")
        self.assertEqual(r["novi"]["trace"]["conclusion"], r["novi"]["text"])
        chat = self.s.chat(0)
        roles = [e["role"] for e in chat["entries"]]
        self.assertIn("user", roles)
        self.assertIn("novi", roles)

    def test_chat_send_strips_heard_marker_before_store(self) -> None:
        self.s.chat_send("[heard] Hello.")
        user_texts = [e["text"] for e in self.s.chat(0)["entries"] if e["role"] == "user"]
        self.assertTrue(any(t == "Hello." for t in user_texts), user_texts)
        self.assertTrue(all("[heard]" not in t for t in user_texts), user_texts)

    def test_state_includes_reasoning_trace(self) -> None:
        st = self.s.state()
        self.assertIn("reasoning_trace", st)
        self.assertIn("conclusion", st["reasoning_trace"])

    def test_knowledge_context_recalls_learned_fact(self) -> None:
        from MAC_BRAIN.models.stt import TranscriptionResult
        self.s.brain.ingest_transcript(TranscriptionResult(
            text="alice moved the door", language="en", confidence=0.9,
            audio_path="", provider="web", model_id="web",
        ))
        ctx = self.s._knowledge_context("what do you know about alice?")
        self.assertIn("alice moved door", ctx)

    def test_listen_requires_real_sensing(self) -> None:
        with self.assertRaises(RuntimeError):
            self.s.listen(1.0)

    def test_state_includes_plan_and_goal_distance(self) -> None:
        self.s.set_goal(x=4.0, y=0.0)
        self.s.step()
        st = self.s.state()
        self.assertIn("plan", st)
        self.assertIsNotNone(st["active_goal"])
        self.assertIn("distance_to_goal", st["active_goal"])
        self.assertGreater(st["active_goal"]["distance_to_goal"], 0)

    def test_learns_user_name_from_conversation(self) -> None:
        from MAC_BRAIN.models.stt import TranscriptionResult
        self.s.brain.ingest_transcript(TranscriptionResult(
            text="Hi novi, its me Vano", language="en", confidence=0.9,
            audio_path="", provider="web", model_id="web",
        ))
        self.assertIn("vano", self.s.brain._entities_in_text("Hi novi, its me Vano"))
        self.assertIn("vano", self.s._known_persons())

    def test_model_switcher(self) -> None:
        m = self.s.model()
        self.assertIn("available", m)
        self.assertTrue(any(
            self.s.llm_model == a or self.s.llm_model + ":latest" == a
            for a in m["available"]
        ))
        target = [x for x in self.s.available_models if x != self.s.llm_model]
        if target:
            r = self.s.switch_model(target[0])
            self.assertEqual(r["current"], target[0])
        with self.assertRaises(ValueError):
            self.s.switch_model("does-not-exist")

    # ── tests that need their own server ──────────────────────────

    def test_chat_carries_conversation_history_across_turns(self) -> None:
        s = self._server(chat_llm=True)
        s._llm_available = True
        captured: dict = {}

        def fake_chat(**kw):
            captured["user"] = kw.get("user", "")
            return "I remember that."

        s._llm_chat = fake_chat
        s.start()
        try:
            s.chat_send("my name is alice")
            s.chat_send("what is my name?")
            payload = json.loads(captured["user"])
            self.assertIn("conversation_so_far", payload)
            self.assertTrue(payload["conversation_so_far"], "expected prior turns")
            self.assertEqual(payload["conversation_so_far"][0]["role"], "user")
            self.assertIn("alice", payload["conversation_so_far"][0]["text"].lower())
        finally:
            s.stop()

    def test_chat_uses_local_llm_when_available(self) -> None:
        s = self._server(chat_llm=True)
        s._llm_available = True
        s._llm_chat = lambda **kw: "I understand you said something."
        s.start()
        try:
            r = s.chat_send("alice moved the door")
            json.dumps(r)
            self.assertTrue(r["llm"])
            self.assertEqual(r["novi"]["trace"]["route"], f"ollama:{s.llm_model}")
        finally:
            s.stop()

    def test_chat_falls_back_to_deterministic_when_llm_down(self) -> None:
        s = self._server(chat_llm=True)
        s._llm_available = False
        s.start()
        try:
            r = s.chat_send("alice moved the door")
            json.dumps(r)
            self.assertFalse(r["llm"])
        finally:
            s.stop()

    def test_reasoning_router_built(self) -> None:
        from MAC_BRAIN.models.router import ReasoningRouter
        s = self._server(reasoning="router")
        s.start()
        try:
            self.assertIsInstance(s.brain.reasoning, ReasoningRouter)
        finally:
            s.stop()

    def test_llm_chat_disables_thinking_for_nemotron(self) -> None:
        import urllib.request
        real = urllib.request.urlopen
        captured = {}

        def fake(req, timeout=120):
            captured["body"] = json.loads(req.data)

            class Resp:
                def read(self):
                    return b'{"message":{"content":"hello"}}'
                def __enter__(self):
                    return self
                def __exit__(self, *exc):
                    return False
            return Resp()

        s = self._server()
        s.start()
        try:
            urllib.request.urlopen = fake
            s.llm_model = "nemotron-3.5-lightning"
            s._llm_chat(system="sys", user="u")
            self.assertIs(captured["body"].get("think"), False)
            s.llm_model = "qwen3.8:latest"
            s._llm_chat(system="sys", user="u")
            self.assertNotIn("think", captured["body"])
        finally:
            urllib.request.urlopen = real
            s.stop()


# ═══════════════════════════════════════════════════════════════════
# Durable store tests — use shared temp DB to avoid per-test overhead
# ═══════════════════════════════════════════════════════════════════

class NoviWebServerDurableTests(unittest.TestCase):
    """Tests that need a durable store (SQLite). Shares one temp DB."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls._db = str(Path(cls._tmp.name) / "web.db")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": self._db, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def test_state_includes_consolidated_summaries(self) -> None:
        s = self._server()
        s.start()
        try:
            s.hear("alice moved the door")
            s.hear("alice likes jazz")
            s.brain.consolidate()
            st = s.state()
            self.assertIn("summaries", st["memory"])
            self.assertTrue(st["memory"]["summaries"], "expected a consolidated summary")
            self.assertIn("alice", st["memory"]["summaries"][0]["content"].lower())
        finally:
            s.stop()

    def test_state_includes_episodic_narrative(self) -> None:
        s = self._server()
        s.start()
        try:
            s.hear("alice moved the door")
            s.hear("alice said hello")
            st = s.state()
            self.assertIn("narrative", st)
            self.assertTrue(st["narrative"], "expected an episodic narrative")
            self.assertTrue(any("alice" in n.lower() for n in st["narrative"]), st["narrative"])
        finally:
            s.stop()

    def test_chat_recalls_consolidated_summaries(self) -> None:
        s = self._server(chat_llm=True)
        s._llm_available = True
        captured: dict = {}

        def fake_chat(**kw):
            captured["user"] = kw.get("user", "")
            return "I remember that alice moved the door."

        s._llm_chat = fake_chat
        s.start()
        try:
            s.hear("alice moved the door")
            s.hear("alice likes jazz")
            s.brain.consolidate()
            self.assertTrue(s._memory_context(), "expected a consolidated summary")
            s.chat_send("what do you remember about alice?")
            self.assertIn("alice", captured["user"].lower())
            self.assertIn("moved", captured["user"].lower())
        finally:
            s.stop()

    def test_chat_includes_episodic_narrative(self) -> None:
        s = self._server(chat_llm=True)
        s._llm_available = True
        captured: dict = {}

        def fake_chat(**kw):
            captured["user"] = kw.get("user", "")
            return "Alice moved the door, then said hello."

        s._llm_chat = fake_chat
        s.start()
        try:
            s.hear("alice moved the door")
            s.hear("alice said hello")
            s.chat_send("what happened?")
            self.assertIn("Recent events", captured["user"])
            self.assertIn("alice", captured["user"].lower())
        finally:
            s.stop()

    def test_chat_persists_across_restart(self) -> None:
        # Use a fresh temp DB so we don't pick up leftovers from other tests.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "chat.db")
            s1 = NoviWebServer(port=0, store_path=db, auto_step=False, chat_llm=False)
            s1.start()
            try:
                s1.chat_send("my name is alice")
            finally:
                s1.stop()

            s2 = NoviWebServer(port=0, store_path=db, auto_step=False, chat_llm=False)
            s2.start()
            try:
                self.assertTrue(s2._chat, "chat thread must be restored after restart")
                self.assertIn("alice", s2._chat[0]["text"].lower())
            finally:
                s2.stop()

    def test_conversation_summarization_trims_and_stores_summary(self) -> None:
        s = self._server()
        s.start()
        try:
            for i in range(8):
                s._append_chat({"role": "user", "text": f"alice says message {i}"})
            s._maybe_summarize_chat(threshold=5, keep_recent=2)
            self.assertLessEqual(len(s._chat), 2, "thread should be trimmed")
            summaries = [
                r["record"] for r in s.brain.memory.active_rows()
                if r["record"].memory_type == "conversation_summary"
            ]
            self.assertTrue(summaries, "expected a conversation summary memory")
            self.assertIn("alice", summaries[0].content.lower())
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()