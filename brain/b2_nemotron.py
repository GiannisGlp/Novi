from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .b2_model_runtime import ModelInvocationRequest, ModelResult, ModelRuntime


NEMOTRON_3_NANO_OMNI_MODEL_ID = "nvidia/nemotron-3-nano-omni-30b-a3b"
NEMOTRON_3_NANO_OMNI_VERSION = "3.0"


class NemotronBackend(Protocol):
    def invoke(self, *, payload: Mapping[str, Any], request: ModelInvocationRequest) -> Any: ...


@dataclass(frozen=True)
class NemotronInput:
    text: str | None = None
    images: tuple[Any, ...] = ()
    audio: tuple[Any, ...] = ()
    video: tuple[Any, ...] = ()
    metadata: Mapping[str, Any] = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "images": list(self.images),
            "audio": list(self.audio),
            "video": list(self.video),
            "metadata": dict(self.metadata or {}),
        }


class NemotronAdapter:
    """Novi adapter for Nemotron 3 Nano Omni.

    The adapter contains no NVIDIA SDK dependency. A concrete local backend is
    injected at runtime, preserving Novi's ModelRuntime boundary and allowing
    Mac/NVIDIA implementations to share the same semantic interface.
    """

    model_id = NEMOTRON_3_NANO_OMNI_MODEL_ID
    model_version = NEMOTRON_3_NANO_OMNI_VERSION

    def __init__(self, runtime: ModelRuntime, backend: NemotronBackend) -> None:
        self.runtime = runtime
        self.backend = backend

    def invoke(self, *, invocation_id: str, artifact_digest: str, runtime_name: str,
               runtime_version: str, hardware: Mapping[str, Any],
               input_data: NemotronInput, correlation_id: str | None = None) -> ModelResult:
        request = ModelInvocationRequest(
            invocation_id=invocation_id,
            model_id=self.model_id,
            model_version=self.model_version,
            artifact_digest=artifact_digest,
            runtime=runtime_name,
            runtime_version=runtime_version,
            hardware=hardware,
            input_schema_version="1.0.0",
            output_schema_version="1.0.0",
            started_at="2026-08-19T00:00:00Z",
            correlation_id=correlation_id,
            input_payload=input_data.as_payload(),
        )
        return self.runtime.invoke(request)


class DeterministicNemotronBackend:
    """CI backend; it validates multimodal payload shape without model inference."""

    def invoke(self, *, payload: Mapping[str, Any], request: ModelInvocationRequest) -> Any:
        return {
            "type": "multimodal_evidence",
            "text_present": payload.get("text") is not None,
            "image_count": len(payload.get("images", [])),
            "audio_count": len(payload.get("audio", [])),
            "video_count": len(payload.get("video", [])),
            "metadata": dict(payload.get("metadata", {})),
        }
