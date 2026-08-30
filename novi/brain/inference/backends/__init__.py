"""Inference backends (plan 12, §2.1, §57).

Only the runtime owns backends; cognition/autonomy never import a backend
directly. The dependency direction is always:

    Novi inference contract -> runtime -> backends

AirLLM was removed by user decision (2026-08-30) — the runtime keeps the
existing (Ollama/local) and mock backends.
"""

from __future__ import annotations

from .base import AbstractInferenceBackend, ModelBackendState
from .existing import ExistingBackend
from .mock import MockBackend

__all__ = [
    "AbstractInferenceBackend",
    "ExistingBackend",
    "MockBackend",
    "ModelBackendState",
]
