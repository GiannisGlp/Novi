import unittest


class TorchvisionDetectorTests(unittest.TestCase):
    def test_module_imports_without_loading_model(self) -> None:
        from novi.brain.models.torchvision_detector import TorchvisionSSDLiteDetector
        self.assertTrue(callable(TorchvisionSSDLiteDetector))

    def _tensor_detector(self):
        """Detector instance without the heavyweight model load (stub preprocess)."""
        import torch

        from novi.brain.models.torchvision_detector import TorchvisionSSDLiteDetector

        det = TorchvisionSSDLiteDetector.__new__(TorchvisionSSDLiteDetector)
        det._preprocess = lambda img: torch.zeros(3, 8, 8)  # noqa: E731
        return det

    def test_to_tensor_decodes_jpeg_bytes(self) -> None:
        import io

        import torch
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (16, 12), color="red").save(buf, format="JPEG")
        tensor = self._tensor_detector()._to_tensor(buf.getvalue())
        self.assertIsInstance(tensor, torch.Tensor)
        self.assertEqual(tuple(tensor.shape), (3, 8, 8))

    def test_to_tensor_rejects_garbage_bytes(self) -> None:
        det = self._tensor_detector()
        with self.assertRaises(TypeError):
            det._to_tensor(b"demo-frame")

    def test_adapter_normalizes_neural_output(self) -> None:
        from novi.brain.models.local_detector import LocalNeuralObjectDetector
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
