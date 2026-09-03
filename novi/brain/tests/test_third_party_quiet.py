"""Tests for the benign third-party startup-noise silencer.

``./scripts/mac-web.sh`` startup prints warnings that all originate in
third-party libraries, not Novi code:

- ``torch/distributed/.../redirects.py`` — "Redirects are currently not
  supported in MacOs" (emitted when ``torchao`` is pulled in transitively
  via sentence-transformers/peft; elastic redirects are unused here).
- ``torch/utils/_pytree.py`` — Enum-subclass ``register_constant``
  deprecation for torchao's ``KernelPreference`` / ``ScaleCalculationMode``
  (upstream torchao issue; Novi never calls ``register_constant``).
- transformers ``Loading weights`` tqdm bar on every MiniLM load.
- OpenCV ``setPreferableTarget ... new graph engine`` warnings when the
  YuNet/SFace models are created (CPU target selection is a no-op there).

The helper below must silence exactly these — genuine errors from the same
loggers must still surface.
"""

from __future__ import annotations

import logging
import unittest

from novi.brain.third_party_quiet import (
    quiet_opencv_model_load,
    quiet_third_party_startup_noise,
)


class QuietStartupNoiseTest(unittest.TestCase):
    def test_drops_exactly_the_known_benign_torch_messages(self) -> None:
        quiet_third_party_startup_noise()
        for logger_name, message in (
            (
                "torch.distributed.elastic.multiprocessing.redirects",
                "NOTE: Redirects are currently not supported in MacOs.",
            ),
            (
                "torch.utils._pytree",
                "<enum 'KernelPreference'> is an Enum subclass and is now natively "
                "supported by torch.compile as an opaque value type. Calling "
                "register_constant() on Enum subclasses is deprecated and will be "
                "an error in a future release.",
            ),
            (
                "torch.utils._pytree",
                "<enum 'ScaleCalculationMode'> is an Enum subclass and is now natively "
                "supported by torch.compile as an opaque value type. Calling "
                "register_constant() on Enum subclasses is deprecated and will be "
                "an error in a future release.",
            ),
        ):
            with self.assertNoLogs(logger_name, level="WARNING"):
                logging.getLogger(logger_name).warning(message)

    def test_keeps_genuine_errors_from_the_same_loggers(self) -> None:
        quiet_third_party_startup_noise()
        for logger_name in (
            "torch.distributed.elastic.multiprocessing.redirects",
            "torch.utils._pytree",
        ):
            with self.assertLogs(logger_name, level="WARNING") as captured:
                logging.getLogger(logger_name).warning("something actually broke: %s", "boom")
            self.assertIn("boom", captured.output[0])

    def test_idempotent_second_call_adds_no_duplicate_filters(self) -> None:
        quiet_third_party_startup_noise()
        before = {
            name: len(logging.getLogger(name).filters)
            for name in (
                "torch.distributed.elastic.multiprocessing.redirects",
                "torch.utils._pytree",
            )
        }
        quiet_third_party_startup_noise()
        after = {
            name: len(logging.getLogger(name).filters)
            for name in (
                "torch.distributed.elastic.multiprocessing.redirects",
                "torch.utils._pytree",
            )
        }
        self.assertEqual(before, after)

    def test_disables_transformers_progress_bar(self) -> None:
        try:
            from transformers.utils.logging import (
                enable_progress_bar,
                is_progress_bar_enabled,
            )
        except ImportError:
            self.skipTest("transformers not installed")
        was_enabled = is_progress_bar_enabled()
        self.addCleanup(enable_progress_bar if was_enabled else lambda: None)
        quiet_third_party_startup_noise()
        self.assertFalse(is_progress_bar_enabled())

    def test_never_raises(self) -> None:
        quiet_third_party_startup_noise()  # must not raise, even re-entered


class QuietOpenCVModelLoadTest(unittest.TestCase):
    def test_sets_error_level_inside_and_restores_after(self) -> None:
        try:
            import cv2
        except ImportError:
            self.skipTest("opencv not installed")
        before = cv2.utils.logging.getLogLevel()
        with quiet_opencv_model_load():
            self.assertEqual(cv2.utils.logging.getLogLevel(), cv2.utils.logging.LOG_LEVEL_ERROR)
        self.assertEqual(cv2.utils.logging.getLogLevel(), before)

    def test_model_creation_still_succeeds_inside(self) -> None:
        from pathlib import Path

        try:
            import cv2
        except ImportError:
            self.skipTest("opencv not installed")
        yunet = Path.home() / ".cache/novi/models/face_detection_yunet_2023mar.onnx"
        sface = Path.home() / ".cache/novi/models/face_recognition_sface_2021dec.onnx"
        if not (yunet.exists() and sface.exists()):
            self.skipTest("face models not cached")
        with quiet_opencv_model_load():
            recognizer = cv2.FaceRecognizerSF.create(str(sface), "")
            detector = cv2.FaceDetectorYN.create(str(yunet), "", (320, 240))
        self.assertIsNotNone(recognizer)
        self.assertIsNotNone(detector)


if __name__ == "__main__":
    unittest.main()
