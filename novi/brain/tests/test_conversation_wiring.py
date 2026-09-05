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


    def test_rementioned_entity_anchors_recency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("I have two dogs, Rex and Max. Rex is older.")
                state = brain.__dict__.get("_conversations", {}).get("user")
            finally:
                brain.stop()
        self.assertIsNotNone(state)
        self.assertEqual(state.anchor.active_entity, "Rex")

    def test_ambiguous_pronoun_names_both_rivals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("I have two dogs, Rex and Max. Rex is older.")
                resp = brain.respond("Is he good with kids?")
            finally:
                brain.stop()
        text = (resp["text"] or "").lower()
        self.assertIn("rex", text)
        self.assertIn("max", text)

    def test_punctuationless_follow_up_resolves(self) -> None:
        # Voice-channel: STT drops punctuation. "What is its range" must
        # still resolve to the anchor, not be swallowed as a slot answer.
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Tell me about the Model Y.")
                resp = brain.respond("What is its range")
            finally:
                brain.stop()
        self.assertIn("model y", (resp["text"] or "").lower())

    def test_leading_filler_does_not_break_memory_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Remember that I prefer dark interiors.")
                resp = brain.respond("uh what interiors do I prefer")
            finally:
                brain.stop()
        self.assertIn("dark", (resp["text"] or "").lower())

    def test_unpunctuated_correction_still_corrects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Tell me about the Model Y.")
                resp = brain.respond("No I meant the Model 3")
            finally:
                brain.stop()
        self.assertIn("model 3", (resp["text"] or "").lower())

    def test_novi_echo_does_not_contaminate_recency(self) -> None:
        # Explicit switch ("forget that, what about BMW?") + "its" must
        # resolve to BMW even though Novi's own echo re-mentions Tesla:
        # the recency cue reads user turns only.
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("Tell me about Tesla.")
                brain.respond("Now forget that. What about BMW?")
                resp = brain.respond("What is its range?")
            finally:
                brain.stop()
        text = (resp["text"] or "").lower()
        self.assertIn("bmw", text)
        self.assertNotIn("tesla", text)
        self.assertNotIn("do you mean", text)

    def test_full_name_beats_shared_head_token(self) -> None:
        # "the Model Y" names Model Y even though "model" also overlaps
        # Model 3; only the bare "the model" is genuinely ambiguous.
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("The Model 3 is small. The Model Y is bigger.")
                named = brain.respond("Tell me about the Model Y.")
                brain2_setup = brain.respond("Tell me about the model.")
            finally:
                brain.stop()
        self.assertIn("model y", (named["text"] or "").lower())
        self.assertNotIn("?", (named["text"] or ""))
        self.assertIn("model 3", (brain2_setup["text"] or "").lower())
        self.assertIn("model y", (brain2_setup["text"] or "").lower())

    def test_anaphoric_preference_value_not_learned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("The Model 3 is small. The Model Y is bigger.")
                brain.respond("I like the bigger one.")
                prefs = [(p.get("kind"), p.get("value"))
                         for p in brain.preferences.snapshot()]
                brain.respond("I like dark interiors.")
                prefs_after = [(p.get("kind"), p.get("value"))
                               for p in brain.preferences.snapshot()]
            finally:
                brain.stop()
        self.assertFalse(any("bigger one" in (v or "") for _, v in prefs))
        self.assertTrue(any("dark interiors" in (v or "") for _, v in prefs_after))

    def test_pronominal_correction_supersedes_stale_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False))
            brain.start()
            try:
                brain.respond("The Model Y has 500 miles of range.")
                brain.respond("Actually it is 330 miles.")
                resp = brain.respond("What did we say the range was?")
            finally:
                brain.stop()
        text = (resp["text"] or "")
        self.assertIn("330", text)
        # History stays auditable: both values named, latest wins.
        self.assertIn("500", text)
        self.assertLess(text.index("500"), text.index("330"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
