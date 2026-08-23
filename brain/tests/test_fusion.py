import tempfile
import unittest
from pathlib import Path

from brain.fusion import ModalityObservation, MultimodalFusion
from brain.engine import MacBrain, MacBrainConfig
from brain.storage import DurableMemoryStore
from brain.tests.test_mac_brain import FakeCamera

T = "2026-08-20T12:00:00Z"


def obs(modality, entity, value, conf, recv=T):
    return ModalityObservation(modality=modality, entity=entity, value=value, confidence=conf, captured_at=recv, received_at=recv, source=modality)


class FusionTests(unittest.TestCase):
    def test_cross_modal_evidence_raises_confidence_and_keeps_provenance(self):
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "alice", "present", 0.6), obs("speech", "alice", "present", 0.6)])
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertGreater(ev.confidence, 0.6)  # two agreeing modalities boost confidence
        self.assertEqual(set(ev.modalities), {"vision", "speech"})
        self.assertEqual(len(ev.contributions), 2)  # provenance preserved

    def test_graceful_degradation_single_modality(self):
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "lamp", "present", 0.7)])
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events[0].confidence, 0.7, places=3)

    def test_conflict_reduces_confidence_and_marks_uncertainty(self):
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "light", "on", 0.9), obs("speech", "light", "off", 0.9)])
        by_value = {e.value: e for e in events}
        self.assertIn("on", by_value)
        self.assertIn("off", by_value)
        for e in events:
            self.assertTrue(e.conflict)
            self.assertLessEqual(e.confidence, 0.5)  # no false certainty on disagreement

    def test_stale_evidence_is_rejected(self):
        f = MultimodalFusion(max_age=5)
        old = obs("vision", "lamp", "present", 0.9, recv="2026-08-20T11:00:00Z")  # 1h old
        new = obs("speech", "alice", "present", 0.7, recv=T)
        events = f.ingest([old, new])
        entities = {e.entity for e in events}
        self.assertIn("alice", entities)
        self.assertNotIn("lamp", entities)  # stale lamp rejected

    def test_deterministic_replay(self):
        inputs = [obs("vision", "a", "present", 0.6), obs("speech", "a", "present", 0.8)]
        f1 = MultimodalFusion(); f2 = MultimodalFusion()
        r1 = [e.snapshot() for e in f1.ingest(inputs)]
        r2 = [e.snapshot() for e in f2.ingest(inputs)]
        self.assertEqual(r1, r2)

    def test_fusion_persists(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "f.db"
            store = DurableMemoryStore(db)
            f = MultimodalFusion()
            f.ingest([obs("vision", "alice", "present", 0.6), obs("speech", "alice", "present", 0.6)])
            store.save_fusion(f.snapshot())
            store.close()
            reopened = DurableMemoryStore(db)
            loaded = MultimodalFusion.from_snapshot(reopened.load_fusion())
            self.assertEqual(len(loaded.recent()), 1)
            self.assertEqual(set(loaded.recent()[0].modalities), {"vision", "speech"})
            reopened.close()


class BrainFusionTests(unittest.TestCase):
    def test_brain_emits_fusion_and_reports_speech_in_result(self):
        from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
        from brain.models.stt import TranscriptionResult

        class PersonBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("person", 0.8, (0, 0, 1, 1)),)

        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        tr = TranscriptionResult(text="hello novi", language="en", confidence=0.9, provider="test", model_id="test", audio_path="")
        brain.ingest_transcript(tr)
        result = brain.step()
        brain.stop()
        self.assertIn("fusion", result)
        self.assertIn("fusion.completed", [e["event_type"] for e in brain.events])
        # speech observation feeds fusion in the following cycle
        speech_fused = [e for e in result["fusion"] if e["entity"] == "speech"]
        self.assertTrue(any(e["value"] == "heard" for e in speech_fused))


if __name__ == "__main__":
    unittest.main()
