"""Inference backend contract (plan 12, §7 Phase 2).

``InferenceBackend`` is the Novi-owned abstract interface every backend —
existing local runtime, AirLLM, future Transformers/vLLM/TensorRT-LLM/llama.cpp —
implements. The contract is deliberately backend-neutral: no CUDA tensors, no
Transformers-only tokenizer APIs, no AirLLM shard names, no HTTP-only or
process-only execution assumptions (plan 12, §57).

Lifecycle is explicit (REGISTERED -> ... -> UNLOADED / FAILED); the runtime
never assumes a model is ready merely because its files exist.
"""

from __future__ import annotations

import abc
from typing import Any, AsyncIterator, Protocol, runtime_checkable

from .capabilities import BackendCapabilities
from .request import InferenceRequest
from .response import InferenceResponse


@runtime_checkable
class InferenceBackend(Protocol):
    """Abstract inference backend contract (plan 12, §7)."""

    @property
    def backend_id(self) -> str: ...

    def capabilities(self) -> BackendCapabilities: ...

    def validate_model(self, model_spec: Any) -> None:
        """Validate that a model spec is acceptable; raise on incompatibility."""

    def prepare(self, model_spec: Any) -> Any:
        """Long-running preparation (e.g. sharding) — a managed deployment op."""

    def load(self, model_spec: Any) -> None: ...

    def unload(self, model_spec: Any) -> None: ...

    def generate(self, request: InferenceRequest) -> InferenceResponse: ...

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceResponse]:
        """Optional streaming; raises BackendProtocolError if unsupported."""
        raise NotImplementedError("streaming not supported")

    def health(self) -> dict[str, Any]: ...

    def metrics(self) -> dict[str, Any]: ...

    def shutdown(self) -> None:
        """Idempotent release of all backend resources."""


class AbstractInferenceBackend(abc.ABC):
    """Convenience ABC for backends; also satisfies ``InferenceBackend``."""

    @property
    @abc.abstractmethod
    def backend_id(self) -> str: ...

    @abc.abstractmethod
    def capabilities(self) -> BackendCapabilities: ...

    @abc.abstractmethod
    def validate_model(self, model_spec: Any) -> None: ...

    @abc.abstractmethod
    def prepare(self, model_spec: Any) -> Any: ...

    @abc.abstractmethod
    def load(self, model_spec: Any) -> None: ...

    @abc.abstractmethod
    def unload(self, model_spec: Any) -> None: ...

    @abc.abstractmethod
    def generate(self, request: InferenceRequest) -> InferenceResponse: ...

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceResponse]:
        raise NotImplementedError("streaming not supported")

    @abc.abstractmethod
    def health(self) -> dict[str, Any]: ...

    def metrics(self) -> dict[str, Any]:
        return {}

    def shutdown(self) -> None:
        """Idempotent default: unload nothing, release nothing."""
        return None
