import unittest


class TorchvisionDetectorTests(unittest.TestCase):
    def test_module_imports_without_loading_model(self) -> None:
        from mac_brain.models.torchvision_detector import TorchvisionSSDLiteDetector

        self.assertTrue(callable(TorchvisionSSDLiteDetector))

    def test_adapter_normalizes_neural_output(self) -> None:
        from mac_brain.models.local_detector import LocalNeuralObjectDetector

        detector = LocalNeuralObjectDetector(
            lambda frame: [{
                "label": "person",
                "confidence": 0.91,
                "bbox": [1, 2, 30, 40],
            }],
            model_id="test-neural",
            runtime="test",
        )
        detections = detector.detect(object())
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "person")
        self.assertAlmostEqual(detections[0].confidence, 0.91)
        self.assertEqual(detections[0].provenance["provider"], "mac.local_neural")


if __name__ == "__main__":
    unittest.main()
