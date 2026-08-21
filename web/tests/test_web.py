import json
import tempfile
import unittest
from pathlib import Path

from web.server import NoviWebServer


class NoviWebServerTests(unittest.TestCase):
    def _server(self, auto_step=False, chat_llm=False):
        return NoviWebServer(port=0, store_path=None, auto_step=auto_step, chat_llm=chat_llm)

    def test_state_and_health_serializable(self):
        s = self._server()
        s.start()
        try:
            st = s.state()
            json.dumps(st)  # must not raise
            self.assertIn("cycle", st)
            self.assertIn("health", st)
            self.assertIn(st["health"]["status"], ("PASS", "WARN", "FAIL", "UNKNOWN"))
        finally:
            s.stop()

    def test_hear_accepts_and_returns_serializable(self):
        s = self._server()
        s.start()
        try:
            r = s.hear("alice moved the door")
            json.dumps(r)
            self.assertTrue(r["accepted"])
            self.assertTrue(r["reasoning"])
        finally:
            s.stop()

    def test_audio_event(self):
        s = self._server()
        s.start()
        try:
            r = s.hear_audio(event_hint="alarm", rms=0.7, confidence=0.9)
            json.dumps(r)
            self.assertIn("alarm", [e["event_type"] for e in r["events"]])
        finally:
            s.stop()

    def test_goal_and_step(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            g = s.set_goal(x=2.0, y=2.0)
            self.assertEqual(g["kind"], "reach")
            self.assertEqual(g["status"], "active")
            step = s.step()
            json.dumps(step)
            self.assertIn("action", step)
        finally:
            s.stop()

    def test_poll_events_increments(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            s.hear("alice is here")
            first = s.poll_events(0)
            self.assertGreater(len(first["events"]), 0)
            after = first["after"]
            second = s.poll_events(after)
            json.dumps(second)
            self.assertGreaterEqual(second["after"], after)
        finally:
            s.stop()

    def test_health(self):
        s = self._server()
        s.start()
        try:
            h = s.health()
            json.dumps(h)
            self.assertIn("status", h)
        finally:
            s.stop()

    def test_chat_send_reflects_message(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            r = s.chat_send("alice moved the door")
            json.dumps(r)
            self.assertTrue(r["accepted"])
            self.assertEqual(r["novi"]["role"], "novi")
            self.assertEqual(r["novi"]["trace"]["conclusion"], r["novi"]["text"])
            # conversation now has a user turn + a novi turn
            chat = s.chat(0)
            roles = [e["role"] for e in chat["entries"]]
            self.assertIn("user", roles)
            self.assertIn("novi", roles)
        finally:
            s.stop()

    def test_state_includes_reasoning_trace(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            st = s.state()
            self.assertIn("reasoning_trace", st)
            self.assertIn("conclusion", st["reasoning_trace"])
        finally:
            s.stop()

    def test_state_includes_consolidated_summaries(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            s = NoviWebServer(port=0, store_path=str(Path(td) / "web.db"), auto_step=False)
            s.start()
            try:
                s.hear("alice moved the door")
                s.hear("alice likes jazz")
                s.brain.consolidate()
                st = s.state()
                self.assertIn("summaries", st["memory"])
                self.assertTrue(st["memory"]["summaries"], "expected a consolidated summary in state")
                self.assertIn("alice", st["memory"]["summaries"][0]["content"].lower())
            finally:
                s.stop()

    def test_chat_recalls_consolidated_summaries(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            s = NoviWebServer(port=0, store_path=str(Path(td) / "web.db"), auto_step=False, chat_llm=True)
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
                self.assertTrue(s._memory_context(), "expected a consolidated summary in memory context")
                s.chat_send("what do you remember about alice?")
                self.assertIn("alice", captured["user"].lower())
                self.assertIn("moved", captured["user"].lower())
            finally:
                s.stop()

    def test_chat_uses_local_llm_when_available(self):
        s = self._server(auto_step=False, chat_llm=True)
        s._llm_available = True
        s._llm_chat = lambda **kw: "I understand you said something — I don't have a memory of that yet."
        s.start()
        try:
            r = s.chat_send("alice moved the door")
            json.dumps(r)
            self.assertTrue(r["llm"])
            self.assertEqual(r["novi"]["trace"]["route"], f"ollama:{s.llm_model}")
            self.assertEqual(r["novi"]["text"], "I understand you said something — I don't have a memory of that yet.")
        finally:
            s.stop()

    def test_chat_falls_back_to_deterministic_when_llm_down(self):
        s = self._server(auto_step=False, chat_llm=True)
        s._llm_available = False
        s.start()
        try:
            r = s.chat_send("alice moved the door")
            json.dumps(r)
            self.assertFalse(r["llm"])
        finally:
            s.stop()

    def test_knowledge_context_recalls_learned_fact(self):
        from MAC_BRAIN.models.stt import TranscriptionResult

        s = self._server(auto_step=False)
        s.start()
        try:
            s.brain.ingest_transcript(TranscriptionResult(text="alice moved the door", language="en", confidence=0.9, audio_path="", provider="web", model_id="web"))
            ctx = s._knowledge_context("what do you know about alice?")
            self.assertIn("alice moved door", ctx)
        finally:
            s.stop()

    def test_reasoning_router_built(self):
        from MAC_BRAIN.models.router import ReasoningRouter

        s = NoviWebServer(port=0, store_path=None, auto_step=False, reasoning="router")
        s.start()
        try:
            self.assertIsInstance(s.brain.reasoning, ReasoningRouter)
        finally:
            s.stop()

    def test_listen_requires_real_sensing(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            with self.assertRaises(RuntimeError):
                s.listen(1.0)
        finally:
            s.stop()

    def test_state_includes_plan_and_goal_distance(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            s.set_goal(x=4.0, y=0.0)
            s.step()
            st = s.state()
            self.assertIn("plan", st)
            self.assertIsNotNone(st["active_goal"])
            self.assertIn("distance_to_goal", st["active_goal"])
            self.assertGreater(st["active_goal"]["distance_to_goal"], 0)
        finally:
            s.stop()

    def test_learns_user_name_from_conversation(self):
        from MAC_BRAIN.models.stt import TranscriptionResult

        s = self._server(auto_step=False)
        s.start()
        try:
            s.brain.ingest_transcript(TranscriptionResult(text="Hi novi, its me Vano", language="en", confidence=0.9, audio_path="", provider="web", model_id="web"))
            # entity extraction now recognizes the new proper noun
            self.assertIn("vano", s.brain._entities_in_text("Hi novi, its me Vano"))
            # identity binding is recorded and surfaced for chat replies
            self.assertIn("vano", s._known_persons())
        finally:
            s.stop()

    def test_llm_chat_disables_thinking_for_nemotron(self):
        import urllib.request
        import json as _json

        captured = {}
        real = urllib.request.urlopen

        def fake(req, timeout=120):
            captured["body"] = _json.loads(req.data)

            class Resp:
                def read(self):
                    return b'{"message":{"content":"hello"}}'
                def __enter__(self):
                    return self
                def __exit__(self, *exc):
                    return False
            return Resp()

        s = self._server(auto_step=False)
        s.start()
        try:
            urllib.request.urlopen = fake
            # Nemotron (a chain-of-thought model) must send top-level think:false
            s.llm_model = "nemotron-3.5-lightning"
            s._llm_chat(system="sys", user="u")
            self.assertIs(captured["body"].get("think"), False)
            # qwen is not a CoT model -> no think field
            s.llm_model = "qwen3.8:latest"
            s._llm_chat(system="sys", user="u")
            self.assertNotIn("think", captured["body"])
        finally:
            urllib.request.urlopen = real
            s.stop()

    def test_model_switcher(self):
        s = self._server(auto_step=False)
        s.start()
        try:
            m = s.model()
            self.assertIn("available", m)
            self.assertTrue(any(s.llm_model == a or s.llm_model + ":latest" == a for a in m["available"]))
            # switch to the first available model and back
            target = [x for x in s.available_models if x != s.llm_model]
            if target:
                r = s.switch_model(target[0])
                self.assertEqual(r["current"], target[0])
            # unknown model must be rejected
            with self.assertRaises(ValueError):
                s.switch_model("does-not-exist")
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
