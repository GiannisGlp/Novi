"""Engine-level tests for event-driven autonomous speech (plan 20, GAP-A/B/C).

A drained non-text event (presence.entered) seeds a proactive utterance through
the salience evaluator → respond_event() → speak() path, gated by the speaking
lease and the event_autonomy_enabled config flag. Deterministic, no hardware.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.models import DeterministicSTTProvider


class FakeCamera:
    def __init__(self) -> None:
        self.n = 0

    def read(self) -> CameraFrame:
        self.n += 1
        return CameraFrame(
            frame_id=f"a-{self.n}", captured_at="t", width=1, height=1,
            payload=b"frame", metadata={"backend": "deterministic"},
        )

    def close(self) -> None:
        return None


class AutonomousSpeechTest(unittest.TestCase):
    def _brain(self, **config_kw) -> MacBrain:
        cfg = MacBrainConfig(curiosity_enabled=False, **config_kw)
        return MacBrain(camera=FakeCamera(), config=cfg)

    def test_presence_event_seeds_autonomous_speech(self) -> None:
        brain = self._brain(event_autonomy_enabled=True)
        brain.start()
        try:
            brain.submit("camera", "presence.entered", {"person": "Alice"})
            step = brain.step()
            self.assertIsNotNone(step.get("autonomous"))
            self.assertEqual(step["autonomous"]["reply_source"], "autonomous")
            emitted = [e for e in brain.events if e["event_type"] == "speech.autonomous"]
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0]["payload"]["kind"], "presence.entered")
        finally:
            brain.stop()

    def test_disabled_by_default_stays_silent(self) -> None:
        brain = self._brain()  # event_autonomy_enabled defaults False
        brain.start()
        try:
            brain.submit("camera", "presence.entered", {"person": "Alice"})
            step = brain.step()
            self.assertIsNone(step.get("autonomous"))
            emitted = [e for e in brain.events if e["event_type"] == "speech.autonomous"]
            self.assertEqual(len(emitted), 0)
        finally:
            brain.stop()

    def test_speaking_lease_suppresses_autonomous_speech(self) -> None:
        brain = self._brain(event_autonomy_enabled=True)
        brain.start()
        try:
            brain.acquire_speaking_lease()
            brain.submit("camera", "presence.entered", {"person": "Alice"})
            step = brain.step()
            self.assertIsNone(step.get("autonomous"))
            suppressed = [e for e in brain.events if e["event_type"] == "speech.initiative_suppressed"]
            self.assertTrue(any(e["payload"].get("reason") == "speaking_lease_held" for e in suppressed))
        finally:
            brain.stop()

    def test_non_salient_event_stays_silent(self) -> None:
        brain = self._brain(event_autonomy_enabled=True)
        brain.start()
        try:
            # scene.changed below the novelty threshold is not worth saying.
            brain.submit("camera", "scene.changed", {"novelty": 0.2})
            step = brain.step()
            self.assertIsNone(step.get("autonomous"))
        finally:
            brain.stop()

    def test_scenario_v1_composed_reply_plus_proactive_same_tick(self) -> None:
        """SCENARIO-V1 + a proactive remark pending in the same tick ⇒ at most
        one utterance: while a reply is being composed (lease held), the
        proactive remark is suppressed and the lease alone gates outbound
        spontaneity (plan 20 §3C)."""
        brain = self._brain(event_autonomy_enabled=True)
        brain.start()
        try:
            # A composed reply is in flight (speaking lease held)…
            brain.acquire_speaking_lease()
            # …while a proactive presence event is also pending this tick.
            brain.submit("camera", "presence.entered", {"person": "Alice"})
            step = brain.step()
            # At most one utterance: the proactive remark is suppressed.
            self.assertIsNone(step.get("autonomous"))
            suppressed = [e for e in brain.events if e["event_type"] == "speech.initiative_suppressed"]
            self.assertTrue(any(e["payload"].get("reason") == "speaking_lease_held" for e in suppressed))
            # The cognitive loop keeps ticking (no stall).
            self.assertGreater(step["cycle"], 0)
        finally:
            brain.stop()

    def test_scene_change_remark_grounded_in_memory(self) -> None:
        """GAP-E: a scene-change remark references prior memory when the entity
        was seen before (durable memory store)."""
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "brain.db"
            brain = MacBrain(
                camera=FakeCamera(),
                config=MacBrainConfig(curiosity_enabled=False, event_autonomy_enabled=True),
                store_path=str(db),
            )
            brain.start()
            try:
                # Seed a memory that mentions the mug.
                brain.ingest_transcript(DeterministicSTTProvider("the red mug is on the counter").transcribe("x.wav"))
                brain.submit("camera", "scene.changed", {"novelty": 0.9, "entity": "mug"})
                step = brain.step()
                self.assertIsNotNone(step.get("autonomous"))
                self.assertIn("mug", step["autonomous"]["text"])
                self.assertIn("I remember", step["autonomous"]["text"])
            finally:
                brain.stop()


if __name__ == "__main__":
    unittest.main()
