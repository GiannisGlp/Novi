"""Silence known-benign third-party startup noise (``./scripts/mac-web.sh``).

Every warning below originates in a third-party library, not Novi code, and
each was verified benign — so the startup log stays clean without hiding
real errors:

- ``torch.distributed.elastic.multiprocessing.redirects`` logs
  "NOTE: Redirects are currently not supported in MacOs" at import time when
  ``torchao`` is pulled in transitively (sentence-transformers, peft).
  Elastic redirectors are unused here.
- ``torch.utils._pytree`` logs an Enum-subclass ``register_constant``
  deprecation for torchao's ``KernelPreference`` / ``ScaleCalculationMode``.
  Upstream torchao issue; Novi never calls ``register_constant``.
- transformers prints a ``Loading weights`` tqdm bar on every MiniLM load.
- OpenCV's DNN backend warns ``setPreferableTarget ... new graph engine``
  when the YuNet/SFace models are created (CPU target selection is a no-op
  under the new graph engine; inference still runs on CPU).

The logging filter drops exactly those messages — any other record from the
same loggers still surfaces. The OpenCV suppression is scoped to model
creation via :func:`quiet_opencv_model_load` so later inference warnings
(if any) are still visible.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

# Exact benign messages (matched as substrings of the formatted record).
_BENIGN_SUBSTRINGS = (
    "Redirects are currently not supported in MacOs",
    "is an Enum subclass and is now natively supported by torch.compile",
)

_NOISY_LOGGERS = (
    "torch.distributed.elastic.multiprocessing.redirects",
    "torch.utils._pytree",
)

_applied = False


class _BenignNoiseFilter(logging.Filter):
    """Drop only the verified-benign third-party startup records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a broken record must never break logging
            return True
        return not any(marker in message for marker in _BENIGN_SUBSTRINGS)


def quiet_third_party_startup_noise() -> None:
    """Install the benign-noise filter and disable load progress bars.

    Idempotent and never raises: safe to call from every lazy heavy-import
    site (MiniLM embedder, trained-adapter loader) as well as server startup.
    """
    global _applied
    if not _applied:
        noise_filter = _BenignNoiseFilter()
        for logger_name in _NOISY_LOGGERS:
            logger = logging.getLogger(logger_name)
            if not any(isinstance(f, _BenignNoiseFilter) for f in logger.filters):
                logger.addFilter(noise_filter)
        _applied = True
    try:
        from transformers.utils.logging import disable_progress_bar  # noqa: PLC0415

        disable_progress_bar()
    except (ImportError, AttributeError):
        pass


@contextmanager
def quiet_opencv_model_load() -> Iterator[None]:
    """Scoped OpenCV log suppression for YuNet/SFace model creation.

    Sets the OpenCV log level to ERROR for the block, then restores the
    previous level — so the benign ``setPreferableTarget`` creation warnings
    stay silent while any later inference warnings remain visible. Yields
    plainly when OpenCV is absent (CI without the vision extra).
    """
    try:
        import cv2  # noqa: PLC0415
    except ImportError:
        yield
        return
    previous = cv2.utils.logging.getLogLevel()
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
    try:
        yield
    finally:
        cv2.utils.logging.setLogLevel(previous)
