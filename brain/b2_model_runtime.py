from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from .contracts import validate_contract, utc_now


class ModelRuntimeError(RuntimeError):
    pass


class ModelAdmissionError(ModelRuntimeError):
    pass


class ModelInvocationError(ModelRuntimeError):
    pass


class ModelBackend(Protocol):
    def load(self, artifact: "ModelArtifact") -> None: ...
    def unload(self, model_id: str) -> None: ...
    def health(self, model_id: str) -> str: ...
    def invoke(self, request: "ModelInvocationRequest") -> Any: ...


@dataclass(frozen=True)
class ModelArtifact:
    model_id: str
    model_version: str
    artifact_digest: str
    uri: str
    backend: str
    runtime_version: str


@dataclass(frozen=True)
class ModelCapabilities:
    modalities: tuple[str, ...] = ()
    input_schema_version: str = "1.0.0"
    output_schema_version: str = "1.0.0"
    supports_cancellation: bool = False
    supports_streaming: bool = False
    stateful: bool = False


@dataclass(frozen=True)
class ModelDescriptor:
    artifact: ModelArtifact
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    resource_class: str = "S4"
    safety_classification: str = "system"
    privacy_classification: str = "inherited"


@dataclass(frozen=True)
class ModelInvocationRequest:
    invocation_id: str
    model_id: str
    model_version: str
    artifact_digest: str
    runtime: str
    runtime_version: str
    hardware: Mapping[str, Any]
    input_schema_version: str
    output_schema_version: str
    started_at: str
    deadline: str | None = None
    priority: str = "P4"
    correlation_id: str | None = None
    trace_id: str | None = None
    resource_class: str = "S4"
    privacy_classification: str = "inherited"
    safety_classification: str = "system"
    input_payload: Any = None

    def contract_payload(self, completed_at: str, latency_ms: float, provenance: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "artifact_digest": self.artifact_digest,
            "runtime": self.runtime,
            "runtime_version": self.runtime_version,
            "hardware": dict(self.hardware),
            "input_schema_version": self.input_schema_version,
            "output_schema_version": self.output_schema_version,
            "started_at": self.started_at,
            "completed_at": completed_at,
            "latency": {"milliseconds": latency_ms},
            "provenance": dict(provenance),
        }


@dataclass(frozen=True)
class ModelResult:
    invocation_id: str
    model_id: str
    model_version: str
    status: str
    output: Any = None
    error_class: str | None = None
    latency_ms: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelHealth:
    model_id: str
    status: str
    reason: str = ""


class DeterministicModelBackend:
    """B2.1 test backend. It deliberately performs no learned inference."""

    def __init__(self) -> None:
        self._loaded: dict[str, ModelArtifact] = {}

    def load(self, artifact: ModelArtifact) -> None:
        self._loaded[artifact.model_id] = artifact

    def unload(self, model_id: str) -> None:
        self._loaded.pop(model_id, None)

    def health(self, model_id: str) -> str:
        return "READY" if model_id in self._loaded else "UNLOADED"

    def invoke(self, request: ModelInvocationRequest) -> Any:
        if request.model_id not in self._loaded:
            raise ModelInvocationError("model_not_loaded")
        return {"echo": request.input_payload}


class ModelRuntime:
    """Backend-neutral B2.1 model execution boundary."""

    def __init__(self, backend: ModelBackend | None = None) -> None:
        self.backend = backend or DeterministicModelBackend()
        self._models: dict[str, ModelDescriptor] = {}

    def register(self, descriptor: ModelDescriptor) -> None:
        if descriptor.artifact.model_id in self._models:
            raise ModelAdmissionError("model_already_registered")
        if not descriptor.artifact.artifact_digest.startswith("sha256:"):
            raise ModelAdmissionError("invalid_artifact_digest")
        self._models[descriptor.artifact.model_id] = descriptor

    def load(self, model_id: str) -> ModelHealth:
        descriptor = self._require(model_id)
        self.backend.load(descriptor.artifact)
        return self.health(model_id)

    def unload(self, model_id: str) -> ModelHealth:
        self._require(model_id)
        self.backend.unload(model_id)
        return self.health(model_id)

    def health(self, model_id: str) -> ModelHealth:
        self._require(model_id)
        return ModelHealth(model_id, self.backend.health(model_id))

    def invoke(self, request: ModelInvocationRequest) -> ModelResult:
        descriptor = self._require(request.model_id)
        artifact = descriptor.artifact
        if request.model_version != artifact.model_version:
            raise ModelInvocationError("model_version_mismatch")
        if request.artifact_digest != artifact.artifact_digest:
            raise ModelInvocationError("artifact_digest_mismatch")
        if request.input_schema_version != descriptor.capabilities.input_schema_version:
            raise ModelInvocationError("input_schema_version_mismatch")
        if request.output_schema_version != descriptor.capabilities.output_schema_version:
            raise ModelInvocationError("output_schema_version_mismatch")

        started = datetime.now(timezone.utc)
        try:
            output = self.backend.invoke(request)
            status = "completed_on_time"
            error_class = None
        except Exception as exc:
            output = None
            status = "failed"
            error_class = type(exc).__name__

        completed = datetime.now(timezone.utc)
        latency_ms = (completed - started).total_seconds() * 1000.0
        provenance = {
            "runtime": request.runtime,
            "runtime_version": request.runtime_version,
            "artifact_digest": request.artifact_digest,
            "backend": artifact.backend,
        }
        validate_contract(
            "novi.model-invocation",
            request.contract_payload(request.started_at if status == "failed" else utc_now(), latency_ms, provenance),
        )
        return ModelResult(
            invocation_id=request.invocation_id,
            model_id=request.model_id,
            model_version=request.model_version,
            status=status,
            output=output,
            error_class=error_class,
            latency_ms=latency_ms,
            provenance=provenance,
        )

    def _require(self, model_id: str) -> ModelDescriptor:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise ModelAdmissionError("unknown_model") from exc
