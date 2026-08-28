"""Tests for novi/brain/salience.py — event salience → autonomous utterance.

Deterministic, hardware-free: novelty threshold, per-kind+entity cooldown,
repeated-event suppression, max-per-window cap, and known/present entity
matching. Pure unit tests; no engine needed.
"""

from __future__ import annotations

import unittest

from novi.brain.salience import (
    CandidateInitiative,
    EventSaliencePolicy,
    SurgeSalienceEvaluator,
)


def _event(kind: str, *, payload: dict | None = None, source: str = "cam") -> dict:
    return {"kind": kind, "source": source, "seq": 1, "payload": payload or {}}


class SurgeSalienceEvaluatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.eval = SurgeSalienceEvaluator()

    def test_presence_entered_known_greets(self) -> None:
        cand = self.eval.evaluate(
            [_event("presence.entered", payload={"person": "Alice"})],
            cycle=1,
            known_entities=["alice"],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.kind, "presence.entered")
        self.assertEqual(cand.entity, "Alice")
        self.assertEqual(cand.affordance, "greet")
        self.assertIn("Alice", cand.text)
        self.assertIn("known=True", cand.reason)

    def test_presence_entered_unknown_marks_new(self) -> None:
        cand = self.eval.evaluate(
            [_event("presence.entered", payload={"person": "Bob"})],
            cycle=1,
            known_entities=["alice"],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertIn("new to me", cand.text)
        self.assertIn("known=False", cand.reason)

    def test_scene_changed_below_threshold_silent(self) -> None:
        cand = self.eval.evaluate(
            [_event("scene.changed", payload={"novelty": 0.3})],
            cycle=1,
        )
        self.assertIsNone(cand)

    def test_scene_changed_above_threshold_comments(self) -> None:
        cand = self.eval.evaluate(
            [_event("scene.changed", payload={"novelty": 0.9, "entity": "your red mug"})],
            cycle=1,
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.affordance, "comment")
        self.assertIn("mug", cand.text)

    def test_presence_left_remembered_notes(self) -> None:
        cand = self.eval.evaluate(
            [_event("presence.left", payload={"person": "Alice"})],
            cycle=1,
            known_entities=["alice"],
            present_entities=[],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.affordance, "note")
        self.assertIn("Alice", cand.text)

    def test_presence_left_still_present_silent(self) -> None:
        cand = self.eval.evaluate(
            [_event("presence.left", payload={"person": "Alice"})],
            cycle=1,
            present_entities=["alice"],
        )
        self.assertIsNone(cand)

    def test_hearing_anomaly_above_threshold_asks(self) -> None:
        cand = self.eval.evaluate(
            [_event("hearing.anomaly", payload={"novelty": 0.8})],
            cycle=1,
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.affordance, "ask")

    def test_object_recognized_comments(self) -> None:
        cand = self.eval.evaluate(
            [_event("object.recognized", payload={"object": "my mug", "label": "cup"})],
            cycle=1,
            known_entities=["my mug"],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.affordance, "comment")
        self.assertEqual(cand.entity, "my mug")
        self.assertIn("mug", cand.text)

    def test_identity_auto_enrolled_asks_for_name(self) -> None:
        cand = self.eval.evaluate(
            [_event("identity.auto_enrolled", payload={"person": "new-person-1"})],
            cycle=1,
            known_entities=["vanya"],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.kind, "identity.auto_enrolled")
        self.assertEqual(cand.affordance, "ask")
        self.assertEqual(cand.entity, "new-person-1")
        self.assertIn("What's your name?", cand.text)
        self.assertIn("known=False", cand.reason)

    def test_person_holding_known_object_comments(self) -> None:
        cand = self.eval.evaluate(
            [_event("person.holding", payload={"person": "Alice", "object": "my mug"})],
            cycle=1,
            known_entities=["alice", "my mug"],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.kind, "person.holding")
        self.assertEqual(cand.affordance, "comment")
        # the entity is the held object, not the person
        self.assertEqual(cand.entity, "my mug")
        self.assertIn("mug", cand.text)
        self.assertIn("object_known=True", cand.reason)

    def test_object_novel_above_threshold_asks(self) -> None:
        cand = self.eval.evaluate(
            [_event("object.novel", payload={"person": "Alice", "object": "new-object-1", "novelty": 1.0})],
            cycle=1,
            known_entities=["alice"],
        )
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand.kind, "object.novel")
        self.assertEqual(cand.affordance, "ask")
        self.assertEqual(cand.entity, "new-object-1")
        self.assertIn("What is it?", cand.text)
        self.assertIn("novelty=1.00", cand.reason)

    def test_unknown_event_kind_ignored(self) -> None:
        cand = self.eval.evaluate([_event("chat", payload={"text": "hi"})], cycle=1)
        self.assertIsNone(cand)

    def test_cooldown_suppresses_repeat(self) -> None:
        ev = _event("presence.entered", payload={"person": "Alice"})
        first = self.eval.evaluate([ev], cycle=1, known_entities=["alice"])
        self.assertIsNotNone(first)
        second = self.eval.evaluate([ev], cycle=2, known_entities=["alice"])
        self.assertIsNone(second)

    def test_cooldown_expires(self) -> None:
        ev = _event("presence.entered", payload={"person": "Alice"})
        self.eval.evaluate([ev], cycle=1, known_entities=["alice"])
        # After the cooldown window, the same event is salient again.
        cand = self.eval.evaluate(
            [ev], cycle=1 + self.eval.policy.cooldown_cycles, known_entities=["alice"]
        )
        self.assertIsNotNone(cand)

    def test_max_per_window_cap(self) -> None:
        policy = EventSaliencePolicy(max_per_window=2)
        ev = SurgeSalienceEvaluator(policy)
        # Two distinct events fill the window.
        self.assertIsNotNone(ev.evaluate(
            [_event("presence.entered", payload={"person": "Alice"})], cycle=1, known_entities=["alice"]
        ))
        self.assertIsNotNone(ev.evaluate(
            [_event("presence.entered", payload={"person": "Bob"})], cycle=2, known_entities=["bob"]
        ))
        # A third distinct event is suppressed by the cap.
        self.assertIsNone(ev.evaluate(
            [_event("presence.entered", payload={"person": "Carol"})], cycle=3, known_entities=["carol"]
        ))

    def test_window_resets_after_window_cycles(self) -> None:
        policy = EventSaliencePolicy(max_per_window=1, window_cycles=10)
        ev = SurgeSalienceEvaluator(policy)
        self.assertIsNotNone(ev.evaluate(
            [_event("presence.entered", payload={"person": "Alice"})], cycle=1, known_entities=["alice"]
        ))
        self.assertIsNone(ev.evaluate(
            [_event("presence.entered", payload={"person": "Bob"})], cycle=2, known_entities=["bob"]
        ))
        # After the window, the cap resets.
        self.assertIsNotNone(ev.evaluate(
            [_event("presence.entered", payload={"person": "Bob"})], cycle=12, known_entities=["bob"]
        ))

    def test_returns_candidate_initiative_shape(self) -> None:
        cand = self.eval.evaluate(
            [_event("identity.recognized", payload={"person": "Alice"})],
            cycle=1,
            known_entities=["alice"],
        )
        self.assertIsInstance(cand, CandidateInitiative)
        assert cand is not None
        self.assertEqual(cand.affordance, "greet")
        self.assertEqual(cand.source_event["kind"], "identity.recognized")


if __name__ == "__main__":
    unittest.main()
