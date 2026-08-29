"""Speaking-lease gating of spontaneous initiative (plan 19, Phase 2).

The web server previously froze the whole background loop with a `_chat_busy`
flag while a reply was being composed, to stop a concurrent step from firing a
duplicate initiative. The north-star fix keeps the loop ticking and instead
gates initiative on a *speaking lease*: while a reply is being composed (the
lease is held), `_maybe_initiate` stays silent; once released, initiative can
fire again. This is the "initiative × speaking-lease fusion" that lets the loop
run continuously (SCENARIO-V1) without duplicate spontaneous remarks.

Pins:
  - `_maybe_initiate` returns None while the speaking lease is held;
  - it fires normally once the lease is released;
  - the lease is a plain, thread-safe acquire/release pair on the brain.
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


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


def _brain(**kw) -> MacBrain:
    cfg = MacBrainConfig(curiosity_enabled=False, initiative_enabled=True, **kw)
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=cfg)


def _initiated(brain: MacBrain) -> list:
    return [e for e in brain.events if e.get("event_type") == "speech.initiated"]


class SpeakingLeaseTests(unittest.TestCase):
    def test_lease_defaults_to_released(self):
        brain = _brain()
        brain.start()
        try:
            self.assertFalse(brain.speaking_lease)
        finally:
            brain.stop()

    def test_acquire_and_release(self):
        brain = _brain()
        brain.start()
        try:
            brain.acquire_speaking_lease()
            self.assertTrue(brain.speaking_lease)
            brain.release_speaking_lease()
            self.assertFalse(brain.speaking_lease)
        finally:
            brain.stop()

    def test_initiative_suppressed_while_lease_held(self):
        """While a reply is being composed (lease held), no spontaneous remark fires."""
        brain = _brain(initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            brain.acquire_speaking_lease()
            for _ in range(6):  # past the neglect threshold
                brain.step()
            self.assertEqual(_initiated(brain), [], "must not initiate while the speaking lease is held")
        finally:
            brain.stop()

    def test_initiative_fires_after_lease_released(self):
        """Once the lease is released, a neglected brain initiates normally."""
        brain = _brain(initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            brain.acquire_speaking_lease()
            for _ in range(6):
                brain.step()
            self.assertEqual(_initiated(brain), [])
            brain.release_speaking_lease()
            for _ in range(6):
                brain.step()
            self.assertEqual(len(_initiated(brain)), 1, "initiative must fire after the lease is released")
        finally:
            brain.stop()

    def test_per_person_lease_scoping(self):
        """Phase 2: one person's lease never blocks another person's stream."""
        brain = _brain()
        brain.start()
        try:
            brain.acquire_speaking_lease("alice")
            self.assertTrue(brain.speaking_lease_for("alice"))
            self.assertFalse(brain.speaking_lease_for("bob"))
            self.assertTrue(brain.speaking_lease, "global view must see any held lease")
            brain.release_speaking_lease("alice")
            self.assertFalse(brain.speaking_lease_for("alice"))
            self.assertFalse(brain.speaking_lease)
        finally:
            brain.stop()

    def test_generic_room_chatter_suppressed_while_any_lease_held(self):
        """No-person (room) initiative must not overlap a directed reply."""
        brain = _brain()
        brain.start()
        try:
            brain.acquire_speaking_lease("alice")
            self.assertTrue(brain.speaking_lease_for(None))
            self.assertTrue(brain.speaking_lease_for(""))
        finally:
            brain.stop()

    def test_respond_holds_lease_for_its_addressee(self):
        """respond() scopes the lease to the resolved addressee, then releases."""
        brain = _brain()
        brain.start()
        try:
            observed: dict = {}

            def llm_chat(*, system: str, user: str, temperature: float = 0.5, timeout: int = 120) -> str:
                observed["lease_during"] = brain.speaking_lease_for("alice")
                observed["other_free"] = not brain.speaking_lease_for("bob")
                return "I remember you, alice — the door moved earlier."

            out = brain.respond("alice, what do you make of the weather?", llm_chat=llm_chat)
            self.assertIsNotNone(out["text"])
            self.assertTrue(observed.get("lease_during"), "lease must be held for alice while composing")
            self.assertTrue(observed.get("other_free"), "bob must stay free while alice's reply composes")
            self.assertFalse(brain.speaking_lease_for("alice"), "lease must be released after the reply")
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
