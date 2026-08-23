"""Phase B1 (gap-audit plan 13): discourse state and anaphora resolution.

Pins:
  - DiscourseState tracks the ongoing topic across turns (bounded window);
  - anaphoric follow-ups ("is it still there?") resolve to the prior topic;
  - anaphoric turns never clobber the tracked topic;
  - a new concrete subject is not treated as anaphora;
  - MacBrain exposes discourse, emits discourse.updated, and respond() passes
    the resolved topic as topic_hint into compose_reply grounding;
  - /api/context serves the discourse snapshot.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.discourse import DiscourseState
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain() -> MacBrain:
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(CupBackend()),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    return brain


def _labels():
    return {"plant", "door", "cup", "kitchen", "shelf", "jazz"}


class DiscourseStateUnitTests(unittest.TestCase):
    def _state(self, window: int = 20) -> DiscourseState:
        return DiscourseState(window=window, known_labels=_labels)

    def test_topic_tracks_concrete_subject(self):
        d = self._state()
        d.observe("let's talk about the plant on the shelf", cycle=1)
        self.assertEqual(d.topic, "plant")

    def test_known_label_preferred_over_longest_word(self):
        d = self._state()
        d.observe("let's talk about the plant on the shelf", cycle=1)
        # Without the label provider the lexical pick would be "let's".
        self.assertNotEqual(d.topic, "let's")

    def test_anaphoric_followup_resolves_to_prior_topic(self):
        d = self._state()
        d.observe("let's talk about the plant on the shelf", cycle=1)
        res = d.resolve("is it still there?")
        self.assertEqual(res.status, "RESOLVED")
        self.assertEqual(res.resolved_topic, "plant")

    def test_unknown_without_prior_topic(self):
        d = self._state()
        res = d.resolve("is it still there?")
        self.assertEqual(res.status, "UNKNOWN")

    def test_no_pronoun_is_none(self):
        d = self._state()
        d.observe("the plant looks great", cycle=1)
        self.assertEqual(d.resolve("where is the door?").status, "NONE")

    def test_new_concrete_subject_not_hijacked(self):
        d = self._state()
        d.observe("the plant needs water", cycle=1)
        # "door" is a concrete new subject — no anaphora resolution.
        self.assertEqual(d.resolve("how about the door").status, "NONE")

    def test_anaphoric_turn_does_not_clobber_topic(self):
        d = self._state()
        d.observe("tell me about jazz", cycle=1)
        d.observe("is it still there?", cycle=2)
        self.assertEqual(d.topic, "jazz")

    def test_window_eviction_bounds_history(self):
        d = DiscourseState(window=20)
        for i in range(30):
            d.observe(f"message number {i} about topic{i}", cycle=i)
        snap = d.snapshot()
        self.assertEqual(len(snap["turns"]), 20)

    def test_snapshot_roundtrip(self):
        import json
        d = DiscourseState()
        d.observe("about the plant again", cycle=3)
        d2 = DiscourseState()
        d2.load_snapshot(json.loads(json.dumps(d.snapshot())))
        self.assertEqual(d2.topic, d.topic)


class BrainDiscourseIntegrationTests(unittest.TestCase):
    def test_brain_has_discourse_and_emits_event(self):
        brain = _brain()
        try:
            out = brain.note_user_message("what is a cup anyway?")
            self.assertIn("status", out)
            events = [e["event_type"] for e in brain.events]
            self.assertIn("discourse.updated", events)
        finally:
            brain.stop()

    def test_note_user_message_resolves_across_calls(self):
        brain = _brain()
        try:
            brain.note_user_message("let's discuss the plant on the shelf")
            out = brain.note_user_message("is it still there?")
            self.assertEqual(out["status"], "RESOLVED")
            self.assertEqual(out["resolved_topic"], "plant")
        finally:
            brain.stop()

    def test_respond_passes_topic_hint_to_compose_reply(self):
        brain = _brain()
        try:
            captured = {}

            def fake_compose_reply(text, **kwargs):
                captured.update(kwargs)
                return {"text": "ok", "fallback": False}

            brain.compose_reply = fake_compose_reply  # type: ignore[method-assign]
            brain.respond("let's discuss the plant on the shelf")
            brain.respond("is it still there?")
            self.assertEqual(captured.get("topic_hint"), "plant")
        finally:
            brain.stop()


class ContextEndpointDiscourseTests(unittest.TestCase):
    def test_context_package_includes_discourse(self):
        from novi.web.server import NoviWebServer
        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        s.start()
        try:
            s.brain.note_user_message("thinking about the plant again")
            ctx = s.context_package()
            self.assertIn("discourse", ctx)
            self.assertEqual(ctx["discourse"].get("topic"), "plant")
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
