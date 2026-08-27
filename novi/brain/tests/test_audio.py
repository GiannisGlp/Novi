import tempfile
import unittest
from pathlib import Path

from novi.brain.audio import AudioFrame, Hearing
from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class HearingTests(unittest.TestCase):
    def setUp(self):
        self.h = Hearing()

    def test_silence(self):
        events = self.h.detect(AudioFrame(rms=0.0))
        self.assertEqual(events[0].event_type, "silence")
        self.assertFalse(events[0].speech)

    def test_speech_vad(self):
        events = self.h.detect(AudioFrame(rms=0.6, speech=True))
        self.assertEqual(events[0].event_type, "speech")
        self.assertTrue(events[0].speech)

    def test_event_hint_classification(self):
        events = self.h.detect(AudioFrame(rms=0.8, event_hint="beep", hint_confidence=0.9))
        self.assertEqual(events[0].event_type, "alarm")

    def test_knock(self):
        events = self.h.detect(AudioFrame(rms=0.6, event_hint="knocking", hint_confidence=0.85))
        self.assertEqual(events[0].event_type, "knock")

    def test_unknown_anomaly(self):
        events = self.h.detect(AudioFrame(rms=0.5, novelty=0.9))
        self.assertEqual(events[0].event_type, "unknown")
        self.assertTrue(events[0].anomaly)

    def test_impulse_energy(self):
        events = self.h.detect(AudioFrame(rms=0.95, novelty=0.1))
        self.assertEqual(events[0].event_type, "impact")

    def test_quality(self):
        q = self.h.quality(AudioFrame(peak=1.0, rms=0.99))
        self.assertTrue(q.clip)
        self.assertTrue(q.saturation)
        q2 = self.h.quality(AudioFrame(peak=0.2, rms=0.0))
        self.assertTrue(q2.silence)
        q3 = self.h.quality(AudioFrame(channel_fault=True))
        self.assertTrue(q3.channel_fault)

    def test_worth_attention(self):
        from novi.brain.audio import AudioEvent
        self.assertTrue(self.h.worth_attention(AudioEvent(event_type="alarm", speech=False, confidence=0.9, intensity=0.3)))
        self.assertFalse(self.h.worth_attention(AudioEvent(event_type="silence", speech=False, confidence=0.5, intensity=0.05)))

    def test_to_observation(self):
        from novi.brain.audio import AudioEvent
        ev = AudioEvent(event_type="knock", speech=False, confidence=0.8, intensity=0.5)
        obs = self.h.to_modality_observation(ev, received_at="2026-01-01T00:00:00+00:00")
        self.assertEqual(obs.modality, "audio")
        self.assertEqual(obs.entity, "knock")


class BrainAudioTests(unittest.TestCase):
    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("person", 0.8, (0, 0, 1, 1)),)

    def _brain(self, db=None):
        return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(self.PersonBackend()), store_path=db, config=MacBrainConfig(curiosity_enabled=False))

    def test_ingest_audio_emits_and_memories(self):
        from novi.brain.audio import AudioFrame
        with tempfile.TemporaryDirectory() as td:
            b = self._brain(str(Path(td) / "b.db"))
            b.start()
            result = b.ingest_audio_frame(AudioFrame(rms=0.8, event_hint="alarm", hint_confidence=0.9, novelty=0.0))
            b.stop()
            self.assertEqual(result["events"][0]["event_type"], "alarm")
            self.assertGreaterEqual(len(result["admitted"]), 1)
            types = [e["event_type"] for e in b.events]
            self.assertIn("hearing.event", types)
            self.assertIn("hearing.quality", types)

    def test_anomaly_emits_event(self):
        from novi.brain.audio import AudioFrame
        b = self._brain()
        b.start()
        b.ingest_audio_frame(AudioFrame(rms=0.5, novelty=0.9))
        b.stop()
        self.assertIn("hearing.anomaly", [e["event_type"] for e in b.events])

    def test_audio_feeds_fusion_and_step_report(self):
        from novi.brain.audio import AudioFrame
        b = self._brain()
        b.start()
        b.ingest_audio_frame(AudioFrame(rms=0.8, event_hint="alarm", hint_confidence=0.9))
        result = b.step()
        b.stop()
        self.assertIn("hearing", result)
        self.assertGreaterEqual(len(result["hearing"]["events"]), 1)
        fused = [e for e in result.get("fusion", []) if e.get("entity") == "alarm"]
        self.assertGreaterEqual(len(fused), 1)
        self.assertIn("audio", fused[0].get("modalities", []))


if __name__ == "__main__":
    unittest.main()
