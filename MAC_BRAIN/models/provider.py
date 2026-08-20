from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from brain.b2_model_runtime import (
    ModelArtifact,
    ModelCapabilities,
    ModelDescriptor,
    ModelInvocationRequest,
    ModelResult,
    ModelRuntime,
)
from brain.b2_real_inference import InferencePolicy, RealModelInvoker


@dataclass(frozen=True)
class MacModelSpec:
    capability: str
    model_id: str
    model_version: str
    artifact_digest: str
    runtime: str
    runtime_version: str
    modalities: tuple[str, ...] = ()


class CallableMacBackend:
    """Adapter for a genuinely local model callable."""

    def __init__(self, model_id: str, fn: Callable[[Any], Any]) -> None:
        self.model_id = model_id
        self.fn = fn
        self.loaded = False

    def health(self, model_id: str) -> str:
        return "READY" if model_id == self.model_id and self.loaded else "UNLOADED"

    def load(self, artifact: ModelArtifact) -> None:
        if artifact.model_id != self.model_id:
            raise ValueError("model_id mismatch")
        self.loaded = True

    def unload(self, model_id: str) -> None:
        if model_id == self.model_id:
            self.loaded = False

    def invoke(self, request: ModelInvocationRequest) -> Any:
        if not self.loaded:
            raise RuntimeError("model_not_loaded")
        return self.fn(request.input_payload)


class MacModelProvider:
    """Capability provider that executes through Novi's existing model runtime."""

    def __init__(self, spec: MacModelSpec, fn: Callable[[Any], Any], policy: InferencePolicy | None = None) -> None:
        self.spec = spec
        self.backend = CallableMacBackend(spec.model_id, fn)
        self.runtime = ModelRuntime(self.backend)
        artifact = ModelArtifact(
            model_id=spec.model_id,
            model_version=spec.model_version,
            artifact_digest=spec.artifact_digest,
            uri=f"local://{spec.model_id}",
            backend=spec.runtime,
            runtime_version=spec.runtime_version,
        )
        descriptor = ModelDescriptor(
            artifact=artifact,
            capabilities=ModelCapabilities(modalities=spec.modalities),
        )
        self.runtime.register(descriptor)
        self.runtime.load(spec.model_id)
        self.invoker = RealModelInvoker(self.runtime, self.backend, policy)

    def health(self) -> str:
        return self.invoker.health(self.spec.model_id)

    def invoke(self, payload: Mapping[str, Any], *, invocation_id: str) -> ModelResult:
        request = ModelInvocationRequest(
            invocation_id=invocation_id,
            model_id=self.spec.model_id,
            model_version=self.spec.model_version,
            artifact_digest=self.spec.artifact_digest,
            runtime=self.spec.runtime,
            runtime_version=self.spec.runtime_version,
            hardware={"target": "mac"},
            input_schema_version="1.0.0",
            output_schema_version="1.0.0",
            started_at="2026-08-19T00:00:00Z",
            input_payload=dict(payload),
        )
        return self.invoker.invoke(request)
