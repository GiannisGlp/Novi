import unittest

from brain.b2_specialist_models import (
    Detection,
    RTDETRAdapter,
    SpecialistModelError,
    StereoDepthAdapter,
)


class B2SpecialistModelTests(unittest.TestCase):
    def test_rtdetr_lifecycle_and_evidence(self) -> None:
        model = RTDETRAdapter()
        self.assertEqual(model.health(), "UNLOADED")
        model.load()
        evidence = model.infer("image", frame_id="frame-1", source_timestamp="2026-08-19T12:00:00Z")
        self.assertEqual(model.health(), "READY")
        self.assertEqual(evidence.model_id, "rtdetr")
        self.assertEqual(len(evidence.detections), 1)
        self.assertEqual(evidence.detections[0].label, "synthetic_object")
        model.unload()
        self.assertEqual(model.health(), "UNLOADED")

    def test_rtdetr_rejects_invalid_detection(self) -> None:
        model = RTDETRAdapter()
        with self.assertRaises(SpecialistModelError):
            model._validate_detection(Detection("bad", 1.1, 0.0, 0.0, 0.5, 0.5))
        with self.assertRaises(SpecialistModelError):
            model._validate_detection(Detection("bad", 0.9, 0.8, 0.0, 0.2, 0.5))

    def test_depth_supports_ess_candidate(self) -> None:
        model = StereoDepthAdapter("ess")
        model.load()
        evidence = model.infer("left", "right", frame_id="frame-2", source_timestamp="2026-08-19T12:00:01Z")
        self.assertEqual(evidence.model_id, "ess")
        self.assertEqual((evidence.width, evidence.height), (2, 2))
        self.assertEqual(len(evidence.disparity), 4)

    def test_depth_supports_foundationstereo_candidate(self) -> None:
        model = StereoDepthAdapter("foundationstereo")
        model.load()
        evidence = model.infer("left", "right", frame_id="frame-3", source_timestamp="2026-08-19T12:00:02Z")
        self.assertEqual(evidence.model_id, "foundationstereo")

    def test_depth_model_choice_is_explicit(self) -> None:
        with self.assertRaises(ValueError):
            StereoDepthAdapter("unknown")

    def test_models_require_load(self) -> None:
        with self.assertRaises(SpecialistModelError):
            RTDETRAdapter().infer("image", frame_id="frame", source_timestamp="now")
        with self.assertRaises(SpecialistModelError):
            StereoDepthAdapter("ess").infer("left", "right", frame_id="frame", source_timestamp="now")


if __name__ == "__main__":
    unittest.main()
