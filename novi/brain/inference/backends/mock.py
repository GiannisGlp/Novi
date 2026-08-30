"""Deterministic mock backend (plan 12, Step 6).

CI-safe, transport-free backend used by tests and as the default when no real
backend is configured. Generates deterministic text from the request; supports
load/unload, streaming, metrics, health, and simulated failures for failure
injection tests (plan 12, §26).
"""

from __future__ import annotations

import time
from typing import Any, AsyncIterator

from ..capabilities import BackendCapabilities, CapabilityState
from ..contracts import AbstractInferenceBackend
from ..errors import GenerationError
from ..request import InferenceRequest
from ..response import FinishReason, InferenceResponse
from .base import ModelBackendState

_BACKEND_ID = "mock"


class MockBackend(AbstractInferenceBackend):
    """Deterministic, dependency-free inference backend."""

    def __init__(
        self,
        *,
        fail_generate: bool = False,
        failure_class: str = "",
        latency_ms: float = 0.0,
        token_scale: float = 1.0,
    ) -> None:
        self._fail_generate = fail_generate
        self._failure_class = failure_class
        self._latency_ms = float(latency_ms)
        self._token_scale = float(token_scale)
        self._state = ModelBackendState()
        self._loads: dict[str, int] = {}
        self._shutdown = False

    @property
    def backend_id(self) -> str:
        return _BACKEND_ID

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            backend_id=_BACKEND_ID,
            streaming=True,
            structured_output=True,
            tool_calling=True,
            max_concurrent_requests=4,
            option_keys=frozenset({"mock_prefix", "mock_suffix"}),
            hardware={"cpu": CapabilityState.SUPPORTED},
        )

    def validate_model(self, model_spec: Any) -> None:
        # Mock accepts anything with an id.
        if not getattr(model_spec, "id", None):
            raise ValueError("model_spec requires an id")

    def prepare(self, model_spec: Any) -> Any:
        return {"prepared": True, "model": getattr(model_spec, "id", "unknown")}

    def load(self, model_spec: Any) -> None:
        model_id = getattr(model_spec, "id", "unknown")
        self._loads[model_id] = self._loads.get(model_id, 0) + 1
        self._state.set_lifecycle(model_id, "LOADED")
        self._state.set_residency(model_id, "WARM")

    def unload(self, model_spec: Any) -> None:
        model_id = getattr(model_spec, "id", "unknown")
        self._state.set_lifecycle(model_id, "UNLOADED")
        self._state.set_residency(model_id, "COLD")

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        if self._shutdown:
            raise GenerationError("mock backend shut down", context={"backend": _BACKEND_ID})
        if self._latency_ms > 0:
            time.sleep(self._latency_ms / 1000.0)
        if self._fail_generate:
            raise GenerationError(
                self._failure_class or "mock generation failure",
                code=self._failure_class or None,
                context={"backend": _BACKEND_ID, "request_id": request.request_id},
            )
        prefix = str(request.backend_options.get("mock_prefix", "mock:"))
        last = request.messages[-1].get("content", "") if request.messages else request.system
        text = f"{prefix}{last} [mock]"
        input_tokens = max(1, int(sum(len(str(m.get("content", ""))) for m in request.messages) / 4))
        output_tokens = max(1, int(self._token_scale * 8))
        return InferenceResponse(
            request_id=request.request_id,
            model_id=request.model_hint or "mock",
            backend_id=_BACKEND_ID,
            trace_id=request.trace_id,
            text=text,
            finish_reason=FinishReason.STOP,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=self._latency_ms,
            time_to_first_token_ms=min(self._latency_ms, 1.0),
            generation_tokens_per_second=output_tokens / max(self._latency_ms / 1000.0, 0.001),
            cache_status="none",
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceResponse]:
        text = self.generate(request).text
        chunks = text.split(" ")
        for i, chunk in enumerate(chunks):
            yield InferenceResponse(
                request_id=request.request_id,
                model_id=request.model_hint or "mock",
                backend_id=_BACKEND_ID,
                trace_id=request.trace_id,
                text=chunk,
                finish_reason=FinishReason.STOP if i == len(chunks) - 1 else "",
                output_tokens=1,
            )

    def health(self) -> dict[str, Any]:
        return {"status": "healthy", "backend": _BACKEND_ID, "loads": dict(self._loads)}

    def metrics(self) -> dict[str, Any]:
        return {"backend": _BACKEND_ID, "loads": dict(self._loads)}

    def shutdown(self) -> None:
        self._shutdown = True
