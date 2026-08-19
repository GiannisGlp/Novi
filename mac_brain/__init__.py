"""Executable Mac Brain integration layer.

This package adapts the existing Novi Brain contracts/runtime to Mac I/O and
keeps device/model implementations behind replaceable interfaces.
"""

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
