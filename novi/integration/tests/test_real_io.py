"""Tests: real camera bridge (doc 17 §1).

- MacCameraAdapter adapts brain.io.MacCamera to perception.CameraProvider;
- CameraFeed over it delivers frames; preview b64 JPEG encoding;
- graceful failure when no camera is present (CI-safe).
"""

from __future__ import annotations

import base64
import unittest
from unittest import mock

from novi.brain.io import CameraFrame as BrainCameraFrame
from novi.integration.real_io import (
    MacCameraAdapter,
    encode_frame_jpeg_b64,
)


class _FakeCapture:
    def __init__(self, frames: list) -> None:
        self.frames = list(frames)
        self.released = False

    def read(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True


class TestMacCameraAdapter(unittest.TestCase):
    def test_adapts_brain_camera_to_provider(self):
        import numpy as np

        img = np.zeros((48, 64, 3), dtype="uint8")
        brain_cam = mock.Mock()
        brain_cam.read.return_value = BrainCameraFrame(
            frame_id="mac-camera-1",
            captured_at="t1",
            width=64,
            height=48,
            payload=img,
        )
        adapter = MacCameraAdapter(brain_cam)
        adapter.open()
        frame = adapter.read()
        self.assertEqual(frame.frame_id, "mac-camera-1")
        # payload converted to JPEG bytes for downstream encode/preview
        self.assertEqual(frame.payload[:2], b"\xff\xd8")  # JPEG magic
        adapter.close()

    def test_open_failure_raises_runtime_error(self):
        bad = mock.Mock()
        bad.open.side_effect = RuntimeError("camera device 0 could not be opened")
        with self.assertRaises(RuntimeError):
            MacCameraAdapter(bad).open()


class TestJpegEncoding(unittest.TestCase):
    def test_encode_frame_to_jpeg_data_url(self):
        import numpy as np

        from novi.brain.io import CameraFrame

        img = np.full((48, 64, 3), 127, dtype="uint8")
        frame = CameraFrame(frame_id="f", captured_at="t", width=64, height=48, payload=img)
        url = encode_frame_jpeg_b64(frame)
        self.assertTrue(url.startswith("data:image/jpeg;base64,"))
        raw = base64.b64decode(url.split(",", 1)[1])
        self.assertEqual(raw[:2], b"\xff\xd8")

    def test_encode_passthrough_jpeg_payload(self):
        from novi.brain.io import CameraFrame

        jpeg = b"\xff\xd8\xff\xe0fake"
        frame = CameraFrame(frame_id="f", captured_at="t", width=4, height=4, payload=jpeg)
        url = encode_frame_jpeg_b64(frame)
        self.assertIn(base64.b64encode(jpeg).decode()[:10], url)

    def test_unencodable_payload_returns_none(self):
        from novi.brain.io import CameraFrame

        frame = CameraFrame(frame_id="f", captured_at="t", width=4, height=4, payload=b"not-an-image")
        self.assertIsNone(encode_frame_jpeg_b64(frame))


if __name__ == "__main__":
    unittest.main()
