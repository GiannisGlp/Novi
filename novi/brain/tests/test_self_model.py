"""Tests for the first-person self-model and capability honesty (rule 7).

Locks in docs/06-soul/01 §6-7: the dialogue layer can access a self-concept
(WHO I AM / WHAT I CAN DO / WHERE I AM / WHAT I'M DOING) and is honest about
degraded capabilities rather than pretending it can perceive/act.
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.self_model import SelfModel, build_self_model


class FakeCamera:
    def __init__(self) -> None:
        self.sequence = 0
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(frame_id=f"f-{self.sequence}", captured_at="2026-08-19T14:00:00Z", width=2, height=2, payload=b"frame", metadata={"backend": "test"})


class PersonBackend:
    def detect(self, frame):
        return (Detection("person", 0.95, (0.0, 0.0, 1.0, 1.0)),)

    def depth(self, frame):
        return None

    def segment(self, frame):
        return None


class SelfModelTests(unittest.TestCase):
    def test_self_model_before_any_step_is_graceful(self):
        brain = MacBrain(camera=FakeCamera())
        sm = brain.self_model()
        # The default body has no object-manipulation actuators, so physical
        # actions are honestly reported as FAIL (no overclaiming).
        self.assertEqual(sm["capabilities"], {"physical_actions": "FAIL"})
        self.assertEqual(sm["mode"], "UNKNOWN")
        self.assertEqual(sm["name"], brain.soul.identity.name)

    def test_self_model_assembles_after_step(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        try:
            brain.step()
            sm = brain.self_model()
            self.assertIn(sm["mode"], ("PASS", "WARN", "FAIL", "UNKNOWN"))
            self.assertTrue(sm["capabilities"], "capabilities should be populated from health checks")
            for key in ("memory", "cognition", "perception", "hearing"):
                self.assertIn(key, sm["capabilities"])
            self.assertIn("embodiment", sm)
            self.assertIn("x_m", sm["embodiment"])
            self.assertIn("tone", sm)
            self.assertIn("traits", sm)
            self.assertIn("values", sm)
        finally:
            brain.stop()

    def test_capability_honesty_in_system_prompt(self):
        brain = MacBrain(camera=FakeCamera())
        prompt = brain._dialogue_system_prompt({"name": "Novi", "tone": "warm"}, {"tier": "unknown", "expression": {}}, capabilities={"perception": "FAIL", "hearing": "WARN"})
        self.assertIn("degraded or unavailable", prompt)
        self.assertIn("perception", prompt)
        self.assertIn("hearing", prompt)

    def test_no_capability_clause_when_all_pass(self):
        brain = MacBrain(camera=FakeCamera())
        prompt = brain._dialogue_system_prompt({"name": "Novi", "tone": "warm"}, {"tier": "unknown", "expression": {}}, capabilities={"perception": "PASS", "hearing": "PASS"})
        self.assertNotIn("degraded or unavailable", prompt)

    def test_can_see_can_hear_properties(self):
        m = SelfModel(name="Novi", persona="", origin="", tone="warm", affect={}, traits={}, values={}, capabilities={"perception": "PASS", "hearing": "FAIL"}, embodiment={}, active_goal=None, mode="WARN")
        self.assertTrue(m.can_see)
        self.assertFalse(m.can_hear)

    def test_physical_actions_honors_body_capabilities(self):
        """Regression: build_self_model read ALLOWED_ACTIONS off the body
        snapshot with getattr() on a dict (always empty), so physical_actions
        was always FAIL even for a body that can manipulate objects."""
        class ManipBody:
            def snapshot(self):
                return {"x_m": 0.0, "y_m": 0.0, "heading_deg": 0.0,
                        "ALLOWED_ACTIONS": ["open", "close", "pick_up", "move_forward"]}
        class FakeBrain:
            def __init__(self):
                self.body = ManipBody()
                self.soul = type("S", (), {"identity": type("I", (), {"name": "Novi", "persona": "", "origin": ""})(),
                                          "tone": lambda self, ctx: {"tone": "warm"},
                                          "affect": type("A", (), {"dimensions": {}})(),
                                          "personality": type("P", (), {"traits": {}, "values": {}})()})()
                self._last_health = None
                self._chat_known_persons = lambda: []
                self._goal_context = lambda: None
        sm = build_self_model(FakeBrain())
        self.assertEqual(sm.capabilities.get("physical_actions"), "PASS")


if __name__ == "__main__":
    unittest.main()
