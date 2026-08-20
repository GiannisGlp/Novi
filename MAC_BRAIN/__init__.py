"""Executable Mac Brain integration layer and program specification."""

from .io import MacCamera, MacMicrophone, MacSpeaker, VirtualBody
from .runtime import MacBrain, MacBrainConfig

__all__ = [
    "MacBrain",
    "MacBrainConfig",
    "MacCamera",
    "MacMicrophone",
    "MacSpeaker",
    "VirtualBody",
]
