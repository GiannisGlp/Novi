"""Novi inference error taxonomy.

Stable Novi-owned errors for the inference runtime (plan 12, §6.4). Every
backend — including AirLLM — must translate its own exceptions into these
categories. A raw backend exception must never leak through ``MacBrain``.

Each error carries a stable ``code``, a human message, and optional diagnostic
context. Diagnostic context is for operators, never for cognition: cognition
must only rely on the error *class* and ``code``.
"""

from __future__ import annotations

from typing import Any


class InferenceError(Exception):
    """Base class for all Novi inference errors."""

    code = "inference_error"

    def __init__(self, message: str, *, code: str | None = None, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.code
        self.context = dict(context or {})

    def as_dict(self) -> dict[str, Any]:
        return {"error": self.code, "message": self.message, "context": self.context}


class InferenceConfigurationError(InferenceError):
    """Invalid or contradictory runtime/backend configuration."""

    code = "inference_configuration_error"


class ModelNotFoundError(InferenceError):
    """The requested model is not present in the registry."""

    code = "model_not_found"


class ModelUnavailableError(InferenceError):
    """The model exists in the registry but is not currently servable."""

    code = "model_unavailable"


class BackendUnavailableError(InferenceError):
    """The selected backend is not available (missing dependency, disabled...)."""

    code = "backend_unavailable"


class BackendInitializationError(InferenceError):
    """The backend failed to initialize (load, prepare, validate)."""

    code = "backend_initialization_error"


class ModelCompatibilityError(InferenceError):
    """The model is not compatible with the selected backend/runtime stack."""

    code = "model_compatibility_error"


class TokenizationError(InferenceError):
    """Tokenization or detokenization failed."""

    code = "tokenization_error"


class ContextLimitError(InferenceError):
    """Input context exceeds the model's validated context limit."""

    code = "context_limit_error"


class DeadlineExceededError(InferenceError):
    """The request exceeded its deadline or latency budget."""

    code = "deadline_exceeded"


class InferenceCancelledError(InferenceError):
    """The request was cancelled (cooperative cancellation at a boundary)."""

    code = "inference_cancelled"


class OutOfMemoryError(InferenceError):
    """RAM/VRAM exhaustion during load or generation."""

    code = "out_of_memory"


class StorageCapacityError(InferenceError):
    """Insufficient disk capacity for preparation, shards, or caches."""

    code = "storage_capacity"


class ShardIntegrityError(InferenceError):
    """Shard files are missing, unexpected, or fail integrity verification."""

    code = "shard_integrity"


class GenerationError(InferenceError):
    """Generation produced no usable output (empty, malformed, backend failure)."""

    code = "generation_error"


class BackendProtocolError(InferenceError):
    """The backend violated the inference contract (unexpected response shape)."""

    code = "backend_protocol_error"


#: Stable taxonomy exposed for tooling/observability.
ERROR_TAXONOMY: tuple[str, ...] = (
    "inference_error",
    "inference_configuration_error",
    "model_not_found",
    "model_unavailable",
    "backend_unavailable",
    "backend_initialization_error",
    "model_compatibility_error",
    "tokenization_error",
    "context_limit_error",
    "deadline_exceeded",
    "inference_cancelled",
    "out_of_memory",
    "storage_capacity",
    "shard_integrity",
    "generation_error",
    "backend_protocol_error",
)

#: Error classes keyed by their stable code, for code -> class translation.
ERROR_BY_CODE: dict[str, type[InferenceError]] = {
    InferenceError.code: InferenceError,
    **{cls.code: cls for cls in InferenceError.__subclasses__()},
}


def classify_backend_exception(exc: BaseException) -> InferenceError:
    """Translate an arbitrary backend exception into a typed Novi error.

    Used as the final fallback inside backend adapters: known backend exception
    types should be translated *explicitly* by the adapter; anything that still
    escapes becomes a generic ``InferenceError`` with a diagnostic context so
    no raw exception leaks upward.
    """
    if isinstance(exc, InferenceError):
        return exc
    return InferenceError(
        str(exc) or type(exc).__name__, code="inference_error", context={"source_type": type(exc).__name__}
    )
