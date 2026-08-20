from __future__ import annotations

from typing import Any

from .object_detection import Detection


class LocalNeuralObjectDetector:
    """Adapter for a real Mac-runnable detector callable."""

    def __init__(self, infer: Any, *, model_id: str, runtime: str) -> None:
        if not callable(infer):
            raise TypeError("infer must be callable")
        self.infer = infer
        self.model_id = model_id
        self.runtime = runtime

    def detect(self, frame: Any) -> tuple[Detection, ...]:
        raw = self.infer(frame)
        results: list[Detection] = []
        for item in raw:
            results.append(
                Detection(
                    label=str(item["label"]),
                    confidence=float(item["confidence"]),
                    bbox=tuple(float(v) for v in item["bbox"]),
                    provenance={
                        "provider": "mac.local_neural",
                        "model_id": self.model_id,
                        "runtime": self.runtime,
                    },
                )
            )
        return tuple(results)
