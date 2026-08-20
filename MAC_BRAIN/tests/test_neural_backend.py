import unittest

from brain.b2_perception import Detection as BrainDetection

from MAC_BRAIN.models.neural_backend import NeuralPerceptionBackend
from MAC_BRAIN.models.object_detection import Detection as MacDetection


class _FakeDetector:
    """Deterministic detector double so the adapter test needs no model download."""

    def __init__(self, detections: tuple[MacDetection, ...] = ()) -> None:
        self._detections = detections

    def detect(self, frame):
        return self._detections


class NeuralPerceptionBackendTests(unittest.TestCase):
    def test_maps_mac_detection_to_brain_detection(self) -> None:
        backend = NeuralPerceptionBackend(detector=_FakeDetector(
            (MacDetection(label="person", confidence=0.92, bbox=(1.0, 2.0, 3.0, 4.0), provenance={"model_id": "fake"}),)
        ))
        result = backend.detect(b"fake-frame")

        self.assertEqual(len(result), 1)
        detection = result[0]
        self.assertIsInstance(detection, BrainDetection)
        self.assertEqual(detection.label, "person")
        self.assertEqual(detection.confidence, 0.92)
        self.assertEqual(detection.bbox_xyxy, (1.0, 2.0, 3.0, 4.0))

    def test_specialist_perception_accepts_neural_backend(self) -> None:
        from brain.b2_perception import SpecialistPerception

        backend = NeuralPerceptionBackend(detector=_FakeDetector(
            (MacDetection(label="tv", confidence=0.6, bbox=(0.0, 0.0, 100.0, 80.0), provenance={"model": "test"}),)
        ))
        perception = SpecialistPerception(backend=backend)
        evidence = perception.process(sensor_id="mac.camera.front", frame_id="f1", timestamp="2026-01-01T00:00:00Z", frame=object())

        self.assertEqual(len(evidence.detections), 1)
        self.assertEqual(evidence.detections[0].label, "tv")
        self.assertEqual(evidence.detections[0].bbox_xyxy, (0.0, 0.0, 100.0, 80.0))

    def test_depth_and_segment_unsupported(self) -> None:
        backend = NeuralPerceptionBackend(detector=_FakeDetector())
        self.assertIsNone(backend.depth(object()))
        self.assertIsNone(backend.segment(object()))


if __name__ == "__main__":
    unittest.main()
