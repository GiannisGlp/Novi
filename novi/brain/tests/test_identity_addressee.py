"""Phase A2 (gap-audit plan 13): identity-first addressee resolution.

Pins the new addressee semantics:
  - a speech self-introduction ("i am Maya") binds the name to the speaker via
    PersonIdentity and becomes the addressee;
  - mentioning a third party does not invent an addressee identity;
  - an explicitly supplied person (vision/voice source) wins;
  - a candidate matching the already-bound speaker name is preferred;
  - respond() routes through resolve_addressee.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.models.stt import TranscriptionResult
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


class ResolveAddresseeTests(unittest.TestCase):
    def test_self_introduction_binds_name_and_returns_addressee(self):
        brain = _brain()
        try:
            addressee = brain.resolve_addressee("hey, i am Maya")
            self.assertEqual(addressee.lower(), "maya")
            belief = brain.identity.identity_for("person")
            self.assertIsNotNone(belief)
            self.assertEqual((belief.name or "").lower(), "maya")
            self.assertEqual(belief.tier, "probable")  # 0.6 >= PROBABLE_CONFIDENCE
            self.assertIn("speech", belief.modalities)
        finally:
            brain.stop()

    def test_third_party_mention_returns_candidate_without_binding(self):
        brain = _brain()
        try:
            addressee = brain.resolve_addressee("is Alice coming to the kitchen?")
            # Legacy fallback may still address the mention, but no identity is bound.
            belief = brain.identity.identity_for("person")
            self.assertTrue(belief is None or belief.name is None)
            self.assertEqual(addressee, "alice")
        finally:
            brain.stop()

    def test_explicit_person_argument_wins(self):
        brain = _brain()
        try:
            self.assertEqual(brain.resolve_addressee("hello there", person="bob"), "bob")
        finally:
            brain.stop()

    def test_bound_speaker_name_preferred_over_new_candidates(self):
        brain = _brain()
        try:
            brain.resolve_addressee("i am Maya")
            # Later message mentioning both the speaker and someone else.
            addressee = brain.resolve_addressee("Maya asked about Alice")
            self.assertEqual(addressee.lower(), "maya")
        finally:
            brain.stop()

    def test_no_candidates_no_binding_empty_addressee(self):
        brain = _brain()
        try:
            self.assertEqual(brain.resolve_addressee("what time is it?"), "")
        finally:
            brain.stop()


class RespondUsesResolverTests(unittest.TestCase):
    def test_respond_routes_through_resolve_addressee(self):
        brain = _brain()
        try:
            out = brain.respond("hi, i am Maya", learn=True)
            self.assertEqual(out["addressee"].lower(), "maya")
            belief = brain.identity.identity_for("person")
            self.assertIsNotNone(belief)
            self.assertEqual((belief.name or "").lower(), "maya")
        finally:
            brain.stop()


class IngestTranscriptIntroductionTests(unittest.TestCase):
    def test_transcript_introduction_binds_via_ingest(self):
        brain = _brain()
        try:
            brain.ingest_transcript(TranscriptionResult(
                text="my name is Georg", language="en", confidence=0.9,
                audio_path="", provider="test", model_id="test",
            ))
            belief = brain.identity.identity_for("person")
            self.assertIsNotNone(belief)
            self.assertEqual((belief.name or "").lower(), "georg")
        finally:
            brain.stop()

    def test_transcript_question_does_not_bind(self):
        brain = _brain()
        try:
            brain.ingest_transcript(TranscriptionResult(
                text="where is Georg?", language="en", confidence=0.9,
                audio_path="", provider="test", model_id="test",
            ))
            belief = brain.identity.identity_for("person")
            self.assertTrue(belief is None or belief.name is None)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
