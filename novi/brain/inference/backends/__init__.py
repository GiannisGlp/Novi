"""Inference backends (plan 12, §2.1, §57).

Only the runtime owns backends; cognition/autonomy never import a backend
directly. The dependency direction is always:

    Novi inference contract -> runtime -> backends
"""

from __future__ import annotations

from .airllm import AirLLMBackend
from .base import AbstractInferenceBackend, ModelBackendState
from .existing import ExistingBackend
from .mock import MockBackend

__all__ = [
    "AbstractInferenceBackend",
    "AirLLMBackend",
    "ExistingBackend",
    "MockBackend",
    "ModelBackendState",
]
