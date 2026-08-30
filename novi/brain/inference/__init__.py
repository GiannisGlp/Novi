"""Novi inference runtime (plan 12).

The inference subsystem is Novi-owned and backend-neutral. Cognition and
autonomy modules import ONLY from this package (or the runtime adapter).
Dependency direction:

    Novi cognition/autonomy -> inference contract -> runtime -> backends
"""

from __future__ import annotations

from .backends import ExistingBackend, MockBackend
from .capabilities import BackendCapabilities, CapabilityState, HardwareProfile, probe_hardware
from .contracts import AbstractInferenceBackend, InferenceBackend
from .errors import (
    BackendInitializationError,
    BackendProtocolError,
    BackendUnavailableError,
    ContextLimitError,
    DeadlineExceededError,
    GenerationError,
    InferenceCancelledError,
    InferenceConfigurationError,
    InferenceError,
    ModelCompatibilityError,
    ModelNotFoundError,
    ModelUnavailableError,
    OutOfMemoryError,
    ShardIntegrityError,
    StorageCapacityError,
    TokenizationError,
)
from .registry import ModelRegistry, ModelSpec
from .request import InferenceRequest, RequestPriority
from .response import FinishReason, InferenceResponse
from .router import ModelRouter, RoutingContext, RoutingDecision
from .runtime import BackendManager, InferenceRuntime, RuntimeConfig
from .scheduler import InferenceScheduler, ScheduledRequest
from .telemetry import InferenceTelemetry

__all__ = [
    "AbstractInferenceBackend",
    "BackendCapabilities",
    "BackendInitializationError",
    "BackendManager",
    "BackendProtocolError",
    "BackendUnavailableError",
    "CapabilityState",
    "ContextLimitError",
    "ExistingBackend",
    "DeadlineExceededError",
    "FinishReason",
    "GenerationError",
    "HardwareProfile",
    "InferenceBackend",
    "InferenceCancelledError",
    "InferenceConfigurationError",
    "InferenceError",
    "InferenceRequest",
    "InferenceResponse",
    "InferenceRuntime",
    "InferenceScheduler",
    "InferenceTelemetry",
    "MockBackend",
    "ModelCompatibilityError",
    "ModelNotFoundError",
    "ModelRegistry",
    "ModelRouter",
    "ModelSpec",
    "ModelUnavailableError",
    "OutOfMemoryError",
    "RequestPriority",
    "RoutingContext",
    "RoutingDecision",
    "RuntimeConfig",
    "ScheduledRequest",
    "ShardIntegrityError",
    "StorageCapacityError",
    "TokenizationError",
    "probe_hardware",
]
