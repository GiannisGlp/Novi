"""Novi Brain — unified implementation (foundational + executable).

This package is the single brain implementation. It contains:

- **Foundational layer** (ported contracts + deterministic doubles): b1_*, b2_*, contracts, runtime (BrainSupervisor)
- **Executable engine** (formerly MAC_BRAIN): engine (Brain/MacBrain), attention, cognition, memory, soul, world, etc.

All code lives under ``brain`` — the ``MAC_BRAIN`` name is retired. Import
via ``brain`` (e.g. ``from brain.engine import Brain``). ``MacBrain`` is kept
as an alias for backward compatibility.
"""

from .b1_cognition import DeterministicCognition, ReasoningResult, Situation
from .b1_memory import DeterministicMemoryManager, MemoryAdmission, MemoryRecord, validate_contract
from .b1_world import SensorObservation, TemporalWorldModel, WorldEntityState, WorldModelState
from .b2_model_runtime import ModelBackend, ModelDescriptor, ModelInvocationRequest, ModelResult, ModelRuntime
from .b2_perception import (
    DepthEstimate,
    Detection,
    DeterministicPerceptionBackend,
    PerceptionBackend,
    SegmentationResult,
    SpecialistPerception,
)
from .b2_real_inference import InferencePolicy, RealModelInvoker
from .contracts import ContractError, ContractRegistry, ContractValidationError, registry, utc_now
from .engine import Brain, BrainConfig, MacBrain, MacBrainConfig
from .io import MacCamera, MacMicrophone, MacSpeaker, VirtualBody
from .runtime import ActionProposal, BrainSupervisor, Lifecycle

__version__ = "0.1.0"

__all__ = [
    # Contracts
    "ContractError",
    "ContractRegistry",
    "ContractValidationError",
    "registry",
    "utc_now",
    # Memory
    "DeterministicMemoryManager",
    "MemoryAdmission",
    "MemoryRecord",
    "validate_contract",
    # Perception
    "DepthEstimate",
    "Detection",
    "DeterministicPerceptionBackend",
    "PerceptionBackend",
    "SegmentationResult",
    "SpecialistPerception",
    # World
    "SensorObservation",
    "TemporalWorldModel",
    "WorldEntityState",
    "WorldModelState",
    # Cognition
    "DeterministicCognition",
    "ReasoningResult",
    "Situation",
    # Model runtime
    "InferencePolicy",
    "ModelBackend",
    "ModelDescriptor",
    "ModelInvocationRequest",
    "ModelResult",
    "ModelRuntime",
    "RealModelInvoker",
    # Brain supervisor (foundational)
    "ActionProposal",
    "BrainSupervisor",
    "Lifecycle",
    # Executable engine (agnostic name + compat)
    "Brain",
    "BrainConfig",
    "MacBrain",
    "MacBrainConfig",
    "MacCamera",
    "MacMicrophone",
    "MacSpeaker",
    "VirtualBody",
]
