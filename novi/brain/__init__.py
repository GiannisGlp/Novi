"""Novi Brain — unified implementation (foundational + executable).

This package is the single brain implementation. It contains:

- **Foundational layer** (ported contracts + deterministic fast-path): b1_*, b2_*, contracts, runtime (BrainSupervisor)
- **Executable engine** (formerly MAC_BRAIN): engine (Brain/MacBrain), attention, cognition, memory, soul, world, etc.

All code lives under ``brain`` — the ``MAC_BRAIN`` name is retired. Import
via ``brain`` (e.g. ``from novi.brain.engine import Brain``). ``MacBrain`` is kept
as an alias for backward compatibility.

**Canonical vs foundational (2026-08-26):** the ``b1_*`` modules hold the
foundational *data types* (``Situation``, ``MemoryRecord``, ``WorldEntityState``,
``SensorObservation``, …) plus deterministic *fast-path* implementations. They are
**not** the canonical cognition/memory/world — those are ``cognition2.MacCognition``,
``storage.DurableMemoryStore``, and ``world_model.WorldModel`` respectively. The
``b1_*`` re-exports below are retained for backward compatibility only; new code
imports the canonical submodules directly.
"""

# Foundational data types + deterministic fast-path (legacy B1 stage) — NOT canonical.
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
