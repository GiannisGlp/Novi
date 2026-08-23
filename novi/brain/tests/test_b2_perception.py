import unittest

from novi.brain.b2_perception import (
    Detection,
    DeterministicPerceptionBackend,
    PerceptionError,
    SpecialistPerception,
)


class FakeBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("person", 0.95, (1.0, 2.0, 10.0, 20.0)),)


class BadConfidenceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("person", 1.5, (1.0, 2.0, 10.0, 20.0)),)


class BadBoxBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("person", 0.9, (10.0, 20.0, 1.0, 2.0)),)


class B2PerceptionTests(unittest.TestCase):
    def test_contract_backend_produces_empty_valid_evidence(self):
        evidence = SpecialistPerception().process(
            sensor_id="camera.front",
            frame_id="frame-1",
            timestamp="2026-08-19T12:00:00Z",
            frame=b"test",
        )
        self.assertEqual(evidence.detections, ())
        self.assertIsNone(evidence.depth)
        self.assertEqual(evidence.provenance["source"], "specialist_perception")

    def test_detection_evidence_is_normalized(self):
        evidence = SpecialistPerception(FakeBackend()).process(
            sensor_id="camera.front",
            frame_id="frame-2",
            timestamp="2026-08-19T12:00:00Z",
            frame=b"test",
        )
        self.assertEqual(evidence.detections[0].label, "person")
        self.assertEqual(evidence.detections[0].confidence, 0.95)
        self.assertEqual(evidence.detections[0].bbox_xyxy, (1.0, 2.0, 10.0, 20.0))

    def test_invalid_confidence_is_rejected(self):
        with self.assertRaises(PerceptionError):
            SpecialistPerception(BadConfidenceBackend()).process(
                sensor_id="camera.front",
                frame_id="frame-3",
                timestamp="2026-08-19T12:00:00Z",
                frame=b"test",
            )

    def test_invalid_bbox_is_rejected(self):
        with self.assertRaises(PerceptionError):
            SpecialistPerception(BadBoxBackend()).process(
                sensor_id="camera.front",
                frame_id="frame-4",
                timestamp="2026-08-19T12:00:00Z",
                frame=b"test",
            )

    def test_backend_is_replaceable(self):
        perception = SpecialistPerception(FakeBackend())
        self.assertEqual(type(perception.backend), FakeBackend)


if __name__ == "__main__":
    unittest.main()
