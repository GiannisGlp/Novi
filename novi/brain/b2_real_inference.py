from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Protocol

from .b2_model_runtime import ModelInvocationRequest, ModelResult, ModelRuntime


class RealInferenceBackend(Protocol):
    """Minimal provider boundary for a real local model server/runtime."""

    def health(self, model_id: str) -> str: ...
    def invoke(self, request: ModelInvocationRequest) -> Any: ...


@dataclass(frozen=True)
class InferencePolicy:
    deadline_ms: int = 5000
    max_output_items: int = 1
    require_structured_output: bool = True


class RealModelInvoker:
    """Runs a real backend through Novi's existing ModelRuntime contract.

    The backend is injected so the semantic Brain layer remains independent of
    vLLM, TensorRT-LLM, llama.cpp, Ollama, CUDA, or a particular NVIDIA GPU.
    """

    def __init__(self, runtime: ModelRuntime, backend: RealInferenceBackend, policy: InferencePolicy | None = None) -> None:
        self.runtime = runtime
        self.backend = backend
        self.policy = policy or InferencePolicy()

    def health(self, model_id: str) -> str:
        return self.backend.health(model_id)

    def invoke(self, request: ModelInvocationRequest) -> ModelResult:
        start = monotonic()
        try:
            output = self.backend.invoke(request)
            elapsed_ms = (monotonic() - start) * 1000.0
            if elapsed_ms > self.policy.deadline_ms:
                return ModelResult(
                    invocation_id=request.invocation_id,
                    model_id=request.model_id,
                    model_version=request.model_version,
                    status="timeout",
                    latency_ms=elapsed_ms,
                    error_class="InferenceDeadlineExceeded",
                    provenance={"backend": request.runtime, "deadline_ms": self.policy.deadline_ms},
                )
            if self.policy.require_structured_output and not isinstance(output, (dict, list)):
                return ModelResult(
                    invocation_id=request.invocation_id,
                    model_id=request.model_id,
                    model_version=request.model_version,
                    status="invalid_output",
                    latency_ms=elapsed_ms,
                    error_class="StructuredOutputRequired",
                    provenance={"backend": request.runtime},
                )
            return ModelResult(
                invocation_id=request.invocation_id,
                model_id=request.model_id,
                model_version=request.model_version,
                status="completed_on_time",
                output=output,
                latency_ms=elapsed_ms,
                provenance={"backend": request.runtime, "deadline_ms": self.policy.deadline_ms},
            )
        except Exception as exc:
            elapsed_ms = (monotonic() - start) * 1000.0
            return ModelResult(
                invocation_id=request.invocation_id,
                model_id=request.model_id,
                model_version=request.model_version,
                status="failed",
                latency_ms=elapsed_ms,
                error_class=type(exc).__name__,
                provenance={"backend": request.runtime},
            )
