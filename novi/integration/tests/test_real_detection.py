"""Tests: real neural object detector (README M1 — SSDLite320 MobileNetV3).

Contract:
- implements perception.ObjectDetector;
- maps torchvision label indices -> COCO category names;
- applies confidence floor; carries frame provenance;
- model injection for CI (fake core); lazy load for real use;
- graceful failure on undecodable payloads.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from novi.brain.io import CameraFrame
from novi.integration.real_io_detection import RealObjectDetector



def _jpeg() -> bytes:
    import cv2
    import numpy as np

    ok, buf = cv2.imencode(".jpg", np.zeros((48, 64, 3), dtype="uint8"))
    assert ok
    return buf.tobytes()


def _frame(payload=None, fid="f1"):
    return CameraFrame(frame_id=fid, captured_at="t", width=64, height=48, payload=payload if payload is not None else _jpeg())


class _FakeCore:
    """Stands in for the torchvision model; emits fixed raw output."""

    categories = ["__background__", "cup", "book", "person"]

    def __init__(self, boxes, scores, labels):
        import numpy as np

        self.out = {
            "boxes": np.array(boxes, dtype="float32"),
            "scores": np.array(scores, dtype="float32"),
            "labels": np.array(labels, dtype="int64"),
        }
        self.calls = 0

    def __call__(self, tensor_list):
        self.calls += 1
        import numpy as np

        # emulate torchvision: dict of stacked tensors keyed the same way
        return [{
            "boxes": np.stack([self.out["boxes"][i] for i in range(len(self.out["scores"]))])
            if len(self.out["scores"]) else np.zeros((0, 4), dtype="float32"),
            "scores": self.out["scores"],
            "labels": self.out["labels"],
        }]


class TestRealObjectDetector(unittest.TestCase):
    def _det(self, core):
        return RealObjectDetector(core=core, confidence_floor=0.60)

    def test_maps_indices_to_coco_names_with_floor(self):
        core = _FakeCore(
            boxes=[[10, 10, 50, 60], [20, 20, 30, 30]],
            scores=[0.91, 0.42],  # second below floor
            labels=[90, 3],
        )
        dets = self._det(core).detect(_frame())
        self.assertEqual([d.label for d in dets], ["cup"])
        self.assertAlmostEqual(dets[0].confidence, 0.91, places=4)
        self.assertEqual(dets[0].bbox, (10, 10, 40, 50))  # x1y1x2y2 -> xywh

    def test_person_label_supported(self):
        core = _FakeCore(boxes=[[5, 5, 60, 90]], scores=[0.87], labels=[1])
        dets = self._det(core).detect(_frame())
        self.assertEqual(dets[0].label, "person")

    def test_frame_provenance_required_and_attached(self):
        core = _FakeCore(boxes=[[0, 0, 10, 10]], scores=[0.9], labels=[1])
        dets = self._det(core).detect(_frame(fid="live-7"))
        self.assertEqual(dets[0].frame_id, "live-7")
        with self.assertRaises(ValueError):
            self._det(_FakeCore([], [], [])).detect(_frame(fid=""))

    def test_empty_predictions_yield_no_detections(self):
        core = _FakeCore(boxes=[], scores=[], labels=[])
        self.assertEqual(self._det(core).detect(_frame()), [])

    def test_protocol_satisfaction(self):
        from novi.perception.detection import ObjectDetector

        self.assertIsInstance(self._det(_FakeCore([], [], [])), ObjectDetector)

    def test_lazy_load_called_once_when_no_core_injected(self):
        det = RealObjectDetector(confidence_floor=0.6)
        calls = {"n": 0}

        def fake_load():
            calls["n"] += 1
            det._core = _FakeCore([], [], [])

        det._load_core = fake_load
        det.detect(_frame())
        det.detect(_frame(fid="f2"))
        self.assertEqual(calls["n"], 1, "model must load lazily exactly once")


if __name__ == "__main__":
    unittest.main()
