import unittest
from pathlib import Path

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

from MAC_BRAIN.io import CameraFrame
from MAC_BRAIN.models import DeterministicSTTProvider
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig


class FakeCamera:
    def __init__(self) -> None:
        self.sequence = 0
        self.closed = False

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"fake-{self.sequence}",
            captured_at="2026-08-19T14:00:00Z",
            width=2,
            height=2,
            payload=b"frame",
            metadata={"backend": "test"},
        )

    def close(self) -> None:
        self.closed = True


class AliceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.95, (0.0, 0.0, 1.0, 1.0)),)


class FakeMicrophone:
    """Deterministic microphone double for STT boundary tests."""

    def __init__(self) -> None:
        self.recorded = []

    def record(self, seconds, output_dir):
        path = output_dir / "fake-mic.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake")
        self.recorded.append((seconds, str(path)))
        from MAC_BRAIN.io import AudioRecording
        return AudioRecording("fake-mic", "2026-01-01T00:00:00Z", path, 16000, 1, seconds)


class DeterministicSTTProviderTests(unittest.TestCase):
    def test_returns_fixed_text(self) -> None:
        provider = DeterministicSTTProvider("hello novi")
        result = provider.transcribe("whatever.wav")
        self.assertEqual(result.text, "hello novi")
        self.assertEqual(result.provider, "deterministic")
        self.assertIn("whatever.wav", result.audio_path)


class SpeechToTextBrainTests(unittest.TestCase):
    def test_listen_runs_through_brain_with_fake_mic_and_deterministic_stt(self) -> None:
        brain = MacBrain(
            camera=FakeCamera(),
            microphone=FakeMicrophone(),
            stt=DeterministicSTTProvider("hello novi"),
        )
        brain.start()
        result = brain.listen(seconds=2.0)
        brain.stop()
        transcription = result["transcription"]
        self.assertEqual(transcription.text, "hello novi")
        self.assertEqual(transcription.provider, "deterministic")
        event_types = [event["event_type"] for event in brain.events]
        self.assertIn("audio.recording.completed", event_types)
        self.assertIn("stt.completed", event_types)

    def test_ingest_transcript_admits_memory_and_reaches_cognition(self) -> None:
        brain = MacBrain(camera=FakeCamera())
        brain.start()
        result = brain.ingest_transcript(DeterministicSTTProvider("alice said hello").transcribe("x.wav"))
        brain.stop()
        self.assertTrue(result["admission"].accepted)
        self.assertEqual(result["admission"].decision, "STORE_EPISODE")
        # speech entity surfaced transiently -> reasoning conclusion
        self.assertEqual(result["reasoning"], "human_speech_observed")
        self.assertEqual(brain.memory.active_count, 1)

    def test_step_admits_perception_to_memory(self) -> None:
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(AliceBackend()))
        brain.start()
        brain.step()
        brain.stop()
        matches = brain.memory.retrieve("alice", memory_type="perception")
        self.assertTrue(matches)
        self.assertIn("alice", matches[0].entity_refs)

    def test_detection_memory_retrievable_by_entity(self) -> None:
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(AliceBackend()))
        brain.start()
        brain.step()
        brain.stop()
        matches = brain.memory.retrieve("alice", memory_type="perception")
        self.assertTrue(matches)
        self.assertIn("alice", matches[0].entity_refs)


class MemoryRecallLoopTests(unittest.TestCase):
    def test_memory_recall_retrieves_relevant_memory_in_loop(self) -> None:
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(AliceBackend()))
        brain.start()
        # store a durable utterance tied to alice
        brain.ingest_transcript(DeterministicSTTProvider("alice said hello").transcribe("x.wav"))
        # next perception cycle reasons with recall context
        brain.step()
        brain.stop()
        recall_events = [e for e in brain.events if e["event_type"] == "memory.recall"]
        self.assertTrue(recall_events)
        payload = recall_events[-1]["payload"]
        self.assertIn("alice", payload["query"])
        self.assertGreaterEqual(payload["recalled"], 1)
        # the reasoning rationale reflects that memory was recalled
        reasoning_events = [e for e in brain.events if e["event_type"] == "reasoning.completed"]
        self.assertTrue(any("recalled" in e["payload"].get("rationale", "") for e in reasoning_events))


class ReasoningActionWiringTests(unittest.TestCase):
    def test_salient_person_drives_observe_action(self) -> None:
        camera = FakeCamera()
        brain = MacBrain(camera=camera, perception=SpecialistPerception(AliceBackend()))
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertEqual(result["detections"], ["alice"])
        self.assertEqual(result["action"], "observe")
        self.assertTrue(result["authorized"])

    def test_person_not_salient_drives_wait_action(self) -> None:
        from brain.b2_perception import Detection

        class PersonBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("person", 0.95, (0.0, 0.0, 1.0, 1.0)),)

        # curiosity disabled: assert the pure reactive conclusion->action mapping
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertEqual(result["detections"], ["person"])
        self.assertEqual(result["action"], "wait")
        self.assertTrue(result["authorized"])


if __name__ == "__main__":
    unittest.main()
