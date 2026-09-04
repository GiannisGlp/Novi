from __future__ import annotations

from typing import Any

from .local_detector import LocalNeuralObjectDetector


class TorchvisionSSDLiteDetector:
    """Real local object detector using torchvision SSDLite320 MobileNetV3."""

    def __init__(self, *, confidence_threshold: float = 0.40, device: str | None = None) -> None:
        try:
            import torch
            from torchvision.models.detection import (
                SSDLite320_MobileNet_V3_Large_Weights,
                ssdlite320_mobilenet_v3_large,
            )
        except ImportError as exc:
            raise RuntimeError(
                "TorchvisionSSDLiteDetector requires torch and torchvision. "
                "Install MAC neural dependencies first."
            ) from exc

        self._torch = torch
        self._weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
        self._model = ssdlite320_mobilenet_v3_large(weights=self._weights).eval()
        self._device = self._select_device(device)
        self._model.to(self._device)
        self._preprocess = self._weights.transforms()
        self._labels = self._weights.meta["categories"]
        self._threshold = confidence_threshold
        self._detector = LocalNeuralObjectDetector(
            self._infer,
            model_id="torchvision:ssdlite320_mobilenet_v3_large",
            runtime=f"pytorch/{torch.__version__}+{self._device}",
        )

    def _select_device(self, requested: str | None) -> Any:
        torch = self._torch
        if requested:
            return torch.device(requested)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @property
    def device(self) -> str:
        return str(self._device)

    @property
    def model_id(self) -> str:
        return "torchvision:ssdlite320_mobilenet_v3_large"

    def detect(self, frame: Any):
        return self._detector.detect(frame)

    def _infer(self, frame: Any) -> list[dict[str, Any]]:
        import torch

        tensor = self._to_tensor(frame)
        with torch.inference_mode():
            output = self._model([tensor.to(self._device)])[0]

        results: list[dict[str, Any]] = []
        boxes = output["boxes"].detach().cpu().tolist()
        scores = output["scores"].detach().cpu().tolist()
        labels = output["labels"].detach().cpu().tolist()
        for box, score, label in zip(boxes, scores, labels, strict=False):
            if score < self._threshold:
                continue
            results.append({
                "label": self._labels[int(label)],
                "confidence": float(score),
                "bbox": tuple(float(v) for v in box),
            })
        return results

    def _to_tensor(self, frame: Any):
        import torch

        if isinstance(frame, torch.Tensor):
            tensor = frame
            if tensor.ndim == 4:
                tensor = tensor[0]
            if tensor.ndim != 3:
                raise ValueError("frame tensor must have shape [C,H,W] or [H,W,C]")
            if tensor.shape[0] not in (1, 3) and tensor.shape[-1] in (1, 3):
                tensor = tensor.permute(2, 0, 1)
            tensor = tensor.float()
            if tensor.max() > 1:
                tensor = tensor / 255.0
            return tensor

        try:
            from io import BytesIO

            from PIL import Image
            if isinstance(frame, (bytes, bytearray)):
                # Encoded image bytes (e.g. a JPEG payload) decode to PIL first.
                frame = Image.open(BytesIO(bytes(frame)))
            image = frame if isinstance(frame, Image.Image) else Image.fromarray(frame)
            return self._preprocess(image.convert("RGB"))
        except Exception as exc:
            raise TypeError(
                "frame must be a PIL image, numpy array, torch tensor, or encoded image bytes"
            ) from exc
