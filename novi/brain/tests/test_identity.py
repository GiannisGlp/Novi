import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.identity import PersonIdentity
from novi.brain.models.stt import TranscriptionResult
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera


class IdentityModelTests(unittest.TestCase):
    def test_detected_when_person_present_but_unnamed(self):
        m = PersonIdentity()
        m.observe("person", confidence=0.8, modality="vision", cycle=1)
        belief = m.identity_for("person")
        self.assertEqual(belief.tier, "detected")
        self.assertIsNone(belief.name)
        self.assertFalse(belief.known)

    def test_naming_raises_to_probable(self):
        m = PersonIdentity()
        m.observe("person", name="alice", confidence=0.7, modality="speech", cycle=2)
        m.observe("person", confidence=0.9, modality="vision", cycle=2)
        belief = m.identity_for("person")
        self.assertEqual(belief.name, "alice")
        self.assertEqual(belief.tier, "probable")

    def test_cross_modal_confident_name_is_verified(self):
        m = PersonIdentity()
        for cycle in range(1, 3):
            m.observe("person", name="alice", confidence=0.9, modality="vision", cycle=cycle)
            m.observe("person", name="alice", confidence=0.9, modality="speech", cycle=cycle)
        belief = m.identity_for("person")
        self.assertEqual(belief.name, "alice")
        self.assertEqual(belief.tier, "verified")
        self.assertTrue(belief.known)
        self.assertGreater(belief.confidence, 0.8)

    def test_unknown_person_returns_none(self):
        m = PersonIdentity()
        self.assertIsNone(m.identity_for("nobody"))

    def test_durability(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "i.db")
            m = PersonIdentity()
            m.observe("person", name="alice", confidence=0.9, modality="speech", cycle=1)
            m.observe("person", confidence=0.9, modality="vision", cycle=1)
            store.save_identity(m.snapshot())
            store.close()
            reopened = DurableMemoryStore(Path(td) / "i.db")
            loaded = PersonIdentity.from_snapshot(reopened.load_identity())
            belief = loaded.identity_for("person")
            self.assertEqual(belief.name, "alice")
            reopened.close()


class BrainIdentityTests(unittest.TestCase):
    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("person", 0.9, (0, 0, 1, 1)),)

    def _brain(self, store_path=None):
        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(self.PersonBackend()),
            store_path=store_path,
            config=MacBrainConfig(curiosity_enabled=False),
        )

    def test_step_observes_person_presence(self):
        brain = self._brain()
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertIn("identity", result)
        self.assertEqual(result["identity"]["tier"], "detected")

    def test_speech_name_binds_identity_and_confirms(self):
        with tempfile.TemporaryDirectory() as td:
            brain = self._brain(store_path=str(Path(td) / "b.db"))
            brain.start()
            brain.step()  # person detected (vision)
            # Only a self-introduction binds the speaker's name (gap-audit A2).
            tr = TranscriptionResult(text="hi, i am alice", language="en", confidence=0.9, audio_path="", provider="test", model_id="test")
            brain.ingest_transcript(tr)
            brain.step()  # vision again + speech binding active
            result = brain.step()
            brain.stop()
            self.assertEqual(result["identity"]["name"], "alice")
            self.assertIn("identity.observed", [e["event_type"] for e in brain.events])
            self.assertIn("identity.named", [e["event_type"] for e in brain.events])

    def test_third_party_mention_does_not_bind_speaker_name(self):
        """Mentioning another person must not invent the speaker's identity."""
        with tempfile.TemporaryDirectory() as td:
            brain = self._brain(store_path=str(Path(td) / "b.db"))
            brain.start()
            tr = TranscriptionResult(text="is alice coming to the kitchen?", language="en", confidence=0.9, audio_path="", provider="test", model_id="test")
            brain.ingest_transcript(tr)
            brain.stop()
            belief = brain.identity.identity_for("person")
            self.assertTrue(belief is None or belief.name is None)
            self.assertNotIn("identity.named", [e["event_type"] for e in brain.events])


if __name__ == "__main__":
    unittest.main()
