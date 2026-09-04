"""Wiring tests: pipeline in respond(), packet render, critic, trace.

Deterministic, socket-free. Uses a real MacBrain on tmp SQLite.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


class _Cam:
    sequence = 0

    def close(self) -> None:
        return None

    def read(self) -> CameraFrame:
        type(self).sequence += 1
        return CameraFrame(frame_id="f", captured_at="t", width=2,
                           height=2, payload=b"f", metadata={})


class WiringTests(unittest.TestCase):
    def test_memory_answer_contains_preference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Remember that I prefer dark interiors.")
                resp = brain.respond("What kind of interiors do I prefer?")
            finally:
                brain.stop()
        self.assertIn("dark", (resp["text"] or "").lower())

    def test_entity_aware_fallback_names_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Tell me about the Model Y.")
                resp = brain.respond("What about the range?")
            finally:
                brain.stop()
        text = (resp["text"] or "").lower()
        self.assertTrue("model y" in text or "tesla" in text,
                        f"entity-aware fallback names the entity: {resp['text']!r}")
        self.assertNotIn("330", text)

    def test_correction_updates_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Tell me about the Model Y.")
                resp = brain.respond("No, I meant the Model 3.")
                convos = brain.__dict__.get("_conversations", {})
                state = convos.get("user")
            finally:
                brain.stop()
        self.assertIsNotNone(state)
        self.assertIn("Model 3", state.anchor.recent_correction)
        self.assertIn("Model 3", resp["text"] or "")
        self.assertEqual(state.anchor.active_entity, "Model 3")

    def test_packet_trace_fields_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                resp = brain.respond("Hi Novi.")
            finally:
                brain.stop()
        conv = (resp.get("trace") or {}).get("conversation") or {}
        self.assertEqual(conv.get("intent", {}).get("intent"), "GREETING")
        self.assertIn("response_goal", conv)
        self.assertIn("critic", conv)
        self.assertIn("packet", resp.get("grounding") or {})

    def test_soft_fallback_on_pipeline_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                with mock.patch(
                        "novi.brain.conversation.context_manager.build_packet",
                        side_effect=RuntimeError("boom")):
                    resp = brain.respond("Hello there.")
            finally:
                brain.stop()
        self.assertTrue(resp["text"])

    def test_greeting_never_asks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                resp = brain.respond("Hi Novi.")
            finally:
                brain.stop()
        text = (resp["text"] or "")
        self.assertNotIn("?", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
