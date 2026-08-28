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

import numpy as np

from novi.perception.real_backends import TorchvisionObjectEmbedder


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
