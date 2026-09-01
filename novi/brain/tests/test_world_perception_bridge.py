"""Tests: perception -> dialogue bridge (plan 26 C).

A web-installed vision provider injects what Novi currently sees into the
world context that grounds replies: a bounded ``perception`` block plus live
entities (person/objects tagged ``source:"camera"``) merged into
``visible_entities`` so the trained ``World:`` line reflects live sight. With
NO provider the world context stays byte-identical to today.
"""

from __future__ import annotations

import json
import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


def _live_provider(*, person: str = "Anna", tier: str = "recognized",
                   objects: tuple[str, ...] = ("blue mug", "cup")):
    def _provider():
        return {
            "camera_live": True,
            "health": "available",
            "recognition_available": True,
            "person": person,
            "person_tier": tier,
            "place": "kitchen",
            "objects": list(objects),
            "scene_labels": ["cup", "person"],
            "last_frame_age_s": 0.05,
            "processed_fps": 12.5,
            "stage_ms": {"detect": 8.0},
            "drop_rate": 0.01,
            "associations": [{"object_ref": "object-my-mug", "label": "my-mug", "places": ["kitchen"]}],
        }

    return _provider


class PersonCupBackend(DeterministicPerceptionBackend):
    """Detects a person and a cup so the unified world has visible entities."""

    def detect(self, frame):
        return (
            Detection("alice", 0.95, (0.0, 0.0, 0.3, 0.5)),
            Detection("cup", 0.85, (0.4, 0.4, 0.6, 0.6)),
        )


def _seeded_brain():
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(PersonCupBackend()),
        config=MacBrainConfig(curiosity_enabled=False, perception_every_n_cycles=1),
    )
    brain.start()
    brain.step()
    return brain


class AssembleWorldContextVisionTests(unittest.TestCase):
    def test_no_provider_world_context_unchanged(self) -> None:
        brain = _seeded_brain()
        try:
            ctx = brain._assemble_world_context("what do you see?", "")
            self.assertGreater(len(ctx.get("visible_entities", [])), 0,
                               "seeded world should have a visible entity")
            self.assertNotIn("perception", ctx, "no provider => no perception block")
        finally:
            brain.stop()

    def test_provider_merges_live_perception_block(self) -> None:
        brain = _seeded_brain()
        try:
            ctx = brain._assemble_world_context(
                "what do you see?", "", vision_provider=_live_provider()
            )
            p = ctx["perception"]
            self.assertTrue(p["camera_live"])
            self.assertEqual(p["person"], "Anna")
            self.assertEqual(p["person_tier"], "recognized")
            self.assertEqual(p["place"], "kitchen")
            self.assertEqual(
                p["objects"],
                [{"label": "blue mug", "kind": "object", "recognized": True},
                 {"label": "cup", "kind": "object", "recognized": True}],
            )
            self.assertEqual(len(p["associations"]), 1)

            labels = [e["label"] for e in ctx["visible_entities"]]
            # live person + objects flow into World: ...
            self.assertIn("Anna", labels)
            self.assertIn("blue mug", labels)
            # ... and the provider's "cup" is deduped against the seeded cup
            self.assertEqual(labels.count("cup"), 1)
            camera_entities = [e for e in ctx["visible_entities"] if e.get("source") == "camera"]
            self.assertEqual({e["type"] for e in camera_entities},
                             {"perception.person", "perception.object"})
        finally:
            brain.stop()

    def test_provider_alone_still_reports_perception_with_empty_world(self) -> None:
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonCupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False, perception_every_n_cycles=1))
        # never stepped: the unified world model has no entities
        ctx = brain._assemble_world_context("hello", "", vision_provider=_live_provider())
        self.assertIn("perception", ctx)
        self.assertEqual(ctx["perception"]["person"], "Anna")
        # no unified-world entities => visible_entities are exactly the live
        # perception set (person + provider objects), camera-tagged
        labels = [e["label"] for e in ctx["visible_entities"]]
        self.assertEqual(labels, ["Anna", "blue mug", "cup"])
        self.assertTrue(all(e.get("source") == "camera" for e in ctx["visible_entities"]))

    def test_throwing_provider_degrades_to_plain_world_context(self) -> None:
        brain = _seeded_brain()
        try:

            def _boom():
                raise RuntimeError("feed broke")

            ctx = brain._assemble_world_context("hi", "", vision_provider=_boom)
            self.assertIn("perception", ctx)
            self.assertFalse(ctx["perception"]["camera_live"])
            # the seeded world entities are preserved
            self.assertGreater(len(ctx.get("visible_entities", [])), 0)
        finally:
            brain.stop()


class ComposeReplyVisionBridgeTests(unittest.TestCase):
    def test_reply_payload_carries_live_perception(self) -> None:
        brain = _seeded_brain()
        brain._vision_provider = _live_provider()
        captured: dict = {}

        def _rec(system: str, user: str) -> str:  # noqa: ARG001
            captured["user"] = user
            return "I can see you, Anna."

        try:
            out = brain._compose_reply_impl("what do you see?", llm_chat=_rec)
            self.assertTrue(out.get("text"))
            payload = json.loads(captured["user"])
            wc = payload["world_context"]
            self.assertEqual(wc["perception"]["person"], "Anna")
            labels = [e["label"] for e in wc["visible_entities"]]
            self.assertIn("Anna", labels)
        finally:
            brain.stop()

    def test_no_provider_payload_has_no_perception(self) -> None:
        brain = _seeded_brain()
        captured: dict = {}

        def _rec(system: str, user: str) -> str:  # noqa: ARG001
            captured["user"] = user
            return "I see a cup."

        try:
            brain._compose_reply_impl("what do you see?", llm_chat=_rec)
            payload = json.loads(captured["user"])
            self.assertNotIn("perception", payload["world_context"])
        finally:
            brain.stop()

    def test_unnamed_incoming_defaults_addressee_to_seen_person(self) -> None:
        brain = _seeded_brain()
        brain._vision_provider = _live_provider()
        sent: dict = {}
        orig = brain.dialogue.reply

        def _spy(**kwargs):
            sent.update(kwargs)
            return orig(**kwargs)

        brain.dialogue.reply = _spy
        try:
            brain._compose_reply_impl("what do you see?", llm_chat=lambda **k: "I can see you.")
            self.assertEqual(sent.get("addressee_name"), "Anna",
                             "a recognized person in view names the addressee")
        finally:
            brain.stop()

    def test_no_provider_keeps_blank_addressee(self) -> None:
        brain = _seeded_brain()
        sent: dict = {}
        orig = brain.dialogue.reply

        def _spy(**kwargs):
            sent.update(kwargs)
            return orig(**kwargs)

        brain.dialogue.reply = _spy
        try:
            brain._compose_reply_impl("what do you see?", llm_chat=lambda **k: "I can see you.")
            self.assertEqual(sent.get("addressee_name"), "",
                             "no provider => no addressee is invented")
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
