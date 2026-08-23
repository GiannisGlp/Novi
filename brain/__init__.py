"""Novi Brain — portable cognitive library (contracts + deterministic test doubles).

This package is NOT the running brain. It provides the foundational types,
contracts and deterministic implementations that the canonical MAC_BRAIN runtime
depends on. The executable brain lives in MAC_BRAIN/ and owns the live loop,
world model, cognition, memory hardening, soul, attention and web bridging
on top of these types.

Dependency direction: MAC_BRAIN → brain  (one-way, never reversed)
Extension rule: do not extend brain/ for new brain features — target MAC_BRAIN/
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
    # Brain supervisor
    "ActionProposal",
    "BrainSupervisor",
    "Lifecycle",
]
