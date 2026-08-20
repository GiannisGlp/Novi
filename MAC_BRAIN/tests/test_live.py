import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

from MAC_BRAIN.io import MacSpeaker
from MAC_BRAIN.live import LiveSession
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class RecordingSpeaker:
    def __init__(self):
        self.spoken = []
        self._available = True

    def available(self) -> bool:
        return self._available

    def speak(self, text: str) -> None:
        self.spoken.append(text)


class LiveSessionTests(unittest.TestCase):
    def _brain(self):
        class PersonBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("person", 0.8, (0, 0, 1, 1)),)

        return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))

    def test_live_round_ends_to_end(self):
        brain = self._brain()
        brain.start()
        speaker = RecordingSpeaker()
        rounds = []
        session = LiveSession(brain=brain, rounds=2, per_round_steps=2, demo_hear="hello novi", speaker=speaker, on_round=lambda i, r: rounds.append(r))
        summary = session.run()
        self.assertEqual(len(summary["rounds"]), 2)
        self.assertTrue(all(r["heard"] == "hello novi" for r in summary["rounds"]))
        self.assertTrue(all("person" in r["steps"][0]["detections"] for r in summary["rounds"]))
        self.assertTrue(all("reply" in r and "tone" in r for r in summary["rounds"]))
        self.assertTrue(all(r["spoke"] for r in summary["rounds"]))
        self.assertGreater(len(speaker.spoken), 0)
        self.assertIn("live.round_completed", [e["event_type"] for e in brain.events])
        self.assertEqual(len(rounds), 2)

    def test_live_degrades_when_speaker_unavailable(self):
        brain = self._brain()
        brain.start()
        speaker = RecordingSpeaker()
        speaker._available = False
        session = LiveSession(brain=brain, rounds=1, demo_hear="hi", speaker=speaker)
        summary = session.run()
        self.assertEqual(len(summary["rounds"]), 1)
        self.assertNotIn("spoke", summary["rounds"][0])  # TTS gracefully skipped

    def test_live_no_hearing_when_demo_hear_none_and_no_mic(self):
        brain = self._brain()
        brain.start()
        brain.microphone = None
        brain.stt = None
        session = LiveSession(brain=brain, rounds=1, demo_hear=None)
        summary = session.run()
        self.assertNotIn("heard", summary["rounds"][0])
        self.assertIn("reply", summary["rounds"][0])

    def test_reply_reflects_tone_and_detections(self):
        brain = self._brain()
        brain.start()
        session = LiveSession(brain=brain, rounds=1, demo_hear="hello")
        summary = session.run()
        reply = summary["rounds"][0]["reply"]
        self.assertIn("person", reply)  # detected entity appears in the reply
        self.assertIn("hello", reply)


class MacSpeakerTests(unittest.TestCase):
    def test_mac_speaker_interface(self):
        speaker = MacSpeaker()
        # `say` presence varies by machine; the interface must just exist
        self.assertTrue(callable(speaker.available))
        self.assertTrue(callable(speaker.speak))


if __name__ == "__main__":
    unittest.main()
