"""Tests: Detection contract + deterministic detector (doc 02 §1).

- Detection: label, confidence, bbox, frame provenance;
- DeterministicObjectDetector: scripted per-frame detections, confidence
  floor filtering — real SSDLite/RT-DETR backends implement the protocol.
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.detection import Detection, DeterministicObjectDetector


def _frame(fid: str = "f1") -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at="t0", width=640, height=480, payload=b"")


class TestDetection:
    def test_bbox_rejects_non_integer_pixels(self):
        with pytest.raises(ValueError):
            Detection(label="cup", confidence=0.9, bbox=(0.5, 0.1, 0.2, 0.2), frame_id="f")

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            Detection(label="cup", confidence=1.4, bbox=(10, 10, 20, 20), frame_id="f")


class TestDeterministicDetector:
    def _detector(self) -> DeterministicObjectDetector:
        return DeterministicObjectDetector(
            scripted={
                "f1": [("cup", 0.91, (100, 100, 80, 120)), ("book", 0.71, (300, 200, 90, 40))],
                "f2": [("cup", 0.62, (105, 102, 80, 120))],
            },
            confidence_floor=0.60,
        )

    def test_detects_scripted_objects_with_provenance(self):
        dets = self._detector().detect(_frame("f1"))
        assert sorted(d.label for d in dets) == ["book", "cup"]
        cup = next(d for d in dets if d.label == "cup")
        assert cup.confidence == 0.91
        assert cup.bbox == (100, 100, 80, 120)
        assert cup.frame_id == "f1"

    def test_confidence_floor_filters_low_scores(self):
        dets = self._detector().detect(_frame("f2"))
        assert [d.label for d in dets] == ["cup"]
        assert all(d.confidence >= 0.60 for d in dets)

    def test_unplanned_frame_yields_no_detections(self):
        assert self._detector().detect(_frame("zz")) == []

    def test_empty_frame_id_rejected(self):
        det = self._detector()
        f = _frame("f1")
        object.__setattr__(f, "frame_id", "")
        with pytest.raises(ValueError):
            det.detect(f)
