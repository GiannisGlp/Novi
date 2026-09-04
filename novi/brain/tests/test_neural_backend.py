import unittest

from novi.brain.b2_perception import Detection as BrainDetection
from novi.brain.models.neural_backend import NeuralPerceptionBackend
from novi.brain.models.object_detection import Detection as MacDetection


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
        from novi.brain.b2_perception import SpecialistPerception

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

    def test_infer_failure_degrades_to_empty_not_raise(self) -> None:
        """A bad frame (e.g. demo-camera bytes with --neural) must degrade to
        no detections — never crash the cognition step."""

        class ExplodingDetector:
            def detect(self, frame):
                raise TypeError("frame must be a PIL image, numpy array, or torch tensor")

        backend = NeuralPerceptionBackend(detector=ExplodingDetector())
        self.assertEqual(backend.detect(b"demo-frame"), ())

    def test_bad_frame_through_specialist_perception_yields_nothing(self) -> None:
        from novi.brain.b2_perception import SpecialistPerception

        class ExplodingDetector:
            def detect(self, frame):
                raise TypeError("boom")

        perception = SpecialistPerception(backend=NeuralPerceptionBackend(detector=ExplodingDetector()))
        evidence = perception.process(
            sensor_id="mac.camera.front", frame_id="f1",
            timestamp="2026-01-01T00:00:00Z", frame=b"demo-frame",
        )
        self.assertEqual(evidence.detections, ())


if __name__ == "__main__":
    unittest.main()
