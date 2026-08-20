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


if __name__ == "__main__":
    unittest.main()
