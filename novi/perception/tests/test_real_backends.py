"""Tests: real perception backends (doc 02 §1-2 concrete providers).

The object embedder (ResNet18 features) is the instance-level counterpart
to the face embedder. Contract:

- `embed(payload, bboxes)` returns one L2-normalized vector per bbox;
- a `core` callable may be injected for CI (no torch/torchvision, no model
  download) — `available` is then True without importing torch;
- honest degradation: undecodable payload -> `[None] * len(bboxes)`;
  `_failed` (no torch) -> `available` False and `embed` returns None per bbox.
"""

from __future__ import annotations

from unittest import mock

import numpy as np

from novi.perception.real_backends import OpenCVFaceEmbedder, TorchvisionObjectEmbedder


def _jpeg() -> bytes:
    import cv2

    ok, buf = cv2.imencode(".jpg", np.zeros((48, 64, 3), dtype="uint8"))
    assert ok
    return buf.tobytes()


def _core(vec: list[float]):
    """Fake ResNet18 core: returns a fixed feature vector for any crop."""

    def _fn(pil_img):
        return list(vec)

    return _fn


class TestObjectEmbedder:
    def test_available_true_with_injected_core(self):
        emb = TorchvisionObjectEmbedder(core=_core([1.0, 0.0]))
        assert emb.available is True

    def test_embed_returns_l2_normalized_vector_per_bbox(self):
        emb = TorchvisionObjectEmbedder(core=_core([3.0, 4.0]))
        vecs = emb.embed(_jpeg(), [(0, 0, 16, 16), (10, 10, 8, 8)])
        assert len(vecs) == 2
        assert vecs[0] is not None
        # L2-normalized: [3,4] -> [0.6, 0.8]
        assert vecs[0][0] == 0.6 and vecs[0][1] == 0.8

    def test_embed_undecodable_payload_returns_none_per_bbox(self):
        emb = TorchvisionObjectEmbedder(core=_core([1.0, 0.0]))
        vecs = emb.embed(b"not-an-image", [(0, 0, 16, 16)])
        assert vecs == [None]

    def test_embed_degenerate_crop_returns_none(self):
        emb = TorchvisionObjectEmbedder(core=_core([1.0, 0.0]))
        # bbox smaller than 8px -> no embedding
        vecs = emb.embed(_jpeg(), [(0, 0, 4, 4)])
        assert vecs == [None]

    def test_failed_backend_degrades_honestly(self):
        emb = TorchvisionObjectEmbedder()
        emb._failed = True
        assert emb.available is False
        assert emb.embed(_jpeg(), [(0, 0, 16, 16)]) == [None]


class _FakeYnet:
    """YuNet-contract stand-in: one face box (x, y, w, h, score...) row."""

    def setInputSize(self, size) -> None:
        self.size = size

    def detect(self, img):
        self.seen = img
        return True, [[40.0, 50.0, 30.0, 40.0, 0.99, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]


class _FakeSFace:
    """SFace-contract stand-in: pass-through crop + fixed 3-d feature."""

    def alignCrop(self, img, face):
        self.seen = (img, face)
        return img

    def feature(self, aligned):
        self._aligned = aligned
        return np.array([0.0, 0.0, 1.0])


class TestFaceEmbedBgr:
    """embed_bgr: the same SFace pipeline over an already-decoded BGR array.

    Plan 26 (A) makes the camera loop decode the JPEG once; the face embedder
    must then run over that decoded array (`embed_bgr`) instead of re-decoding.
    """

    def test_embed_delegates_to_embed_bgr_after_single_decode(self):
        emb = OpenCVFaceEmbedder()
        seen: list[np.ndarray] = []

        def fake_bgr(img):
            seen.append(img)
            return ([float(i) for i in range(128)], (2, 2, 8, 8))

        emb.embed_bgr = fake_bgr  # type: ignore[method-assign]
        with mock.patch.object(
            OpenCVFaceEmbedder, "available", new_callable=mock.PropertyMock, return_value=True
        ):
            vec, bbox = emb.embed(_jpeg())
        assert len(seen) == 1, "embed() decodes once then delegates to embed_bgr"
        assert seen[0].shape[:2] == (48, 64), "the SAME JPEG array, no re-encode"
        assert bbox == (2, 2, 8, 8)
        assert len(vec) == 128

    def test_embed_bgr_unavailable_returns_none(self):
        emb = OpenCVFaceEmbedder()
        with mock.patch.object(
            OpenCVFaceEmbedder, "available", new_callable=mock.PropertyMock, return_value=False
        ):
            assert emb.embed_bgr(np.zeros((64, 64, 3), dtype="uint8")) == (None, None)

    def test_embed_bgr_runs_pipeline_over_the_passed_array(self):
        emb = OpenCVFaceEmbedder()
        emb._detector = _FakeYnet()
        emb._recognizer = _FakeSFace()
        img = np.zeros((96, 128, 3), dtype="uint8")
        with mock.patch.object(
            OpenCVFaceEmbedder, "available", new_callable=mock.PropertyMock, return_value=True
        ):
            vec, bbox = emb.embed_bgr(img)
        assert emb._detector.seen is img, "embed_bgr must not copy or re-decode the array"
        assert emb._detector.size == (128, 96)  # setInputSize((w, h))
        assert bbox == (40, 50, 30, 40)
        assert vec == [0.0, 0.0, 1.0]
