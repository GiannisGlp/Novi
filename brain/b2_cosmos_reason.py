from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .b2_model_runtime import ModelInvocationRequest, ModelResult, ModelRuntime


class CosmosReasonBackend(Protocol):
    def invoke(self, request: ModelInvocationRequest) -> Any: ...


@dataclass(frozen=True)
class CosmosReasonRequest:
    invocation_id: str
    video: Any
    question: str
    timestamp_context: tuple[float, ...] = ()
    correlation_id: str | None = None


class CosmosReason2Adapter:
    """Backend-neutral adapter for Cosmos Reason2 physical reasoning.

    The adapter normalizes physical reasoning into evidence. It does not create
    ActionProposal objects and has no authorization or actuator access.
    """

    MODEL_ID = "cosmos-reason2"
    MODEL_VERSION = "2.0"
    INPUT_SCHEMA = "cosmos-reason2.input/1.0.0"
    OUTPUT_SCHEMA = "cosmos-reason2.output/1.0.0"

    def __init__(self, runtime: ModelRuntime, backend: CosmosReasonBackend) -> None:
        self.runtime = runtime
        self.backend = backend

    def reason(self, request: CosmosReasonRequest) -> ModelResult:
        normalized = ModelInvocationRequest(
            invocation_id=request.invocation_id,
            model_id=self.MODEL_ID,
            model_version=self.MODEL_VERSION,
            artifact_digest="sha256:external-runtime",
            runtime="cosmos-reason2",
            runtime_version=self.MODEL_VERSION,
            hardware={"managed_by": "backend"},
            input_schema_version=self.INPUT_SCHEMA,
            output_schema_version=self.OUTPUT_SCHEMA,
            started_at="1970-01-01T00:00:00Z",
            correlation_id=request.correlation_id,
            input_payload={
                "video": request.video,
                "question": request.question,
                "timestamp_context": request.timestamp_context,
            },
        )
        try:
            output = self.backend.invoke(normalized)
            if not isinstance(output, Mapping):
                raise TypeError("cosmos_reason2_output_must_be_mapping")
            return ModelResult(
                invocation_id=request.invocation_id,
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                status="completed_on_time",
                output=dict(output),
                provenance={
                    "model_family": "Cosmos-Reason2",
                    "role": "physical_reasoning",
                    "adapter": "novi.b2_cosmos_reason",
                },
            )
        except Exception as exc:
            return ModelResult(
                invocation_id=request.invocation_id,
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                status="failed",
                error_class=type(exc).__name__,
                provenance={
                    "model_family": "Cosmos-Reason2",
                    "role": "physical_reasoning",
                    "adapter": "novi.b2_cosmos_reason",
                },
            )

    @staticmethod
    def to_evidence(result: ModelResult) -> dict[str, Any]:
        if result.status != "completed_on_time":
            raise ValueError("cannot_create_evidence_from_failed_reasoning")
        return {
            "source": result.model_id,
            "model_version": result.model_version,
            "kind": "physical_reasoning",
            "payload": result.output,
            "provenance": dict(result.provenance),
        }
