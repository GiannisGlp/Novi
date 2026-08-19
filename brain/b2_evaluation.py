from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Any, Mapping


@dataclass(frozen=True)
class InferenceProvenance:
    invocation_id: str
    model_id: str
    model_version: str
    artifact_digest: str
    runtime: str
    backend: str
    input_schema_version: str
    output_schema_version: str


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    modality: str
    input_payload: Any
    expected_properties: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    status: str
    output_digest: str
    latency_ms: float | None
    provenance: InferenceProvenance
    checks: Mapping[str, bool]


class InferenceEvaluationHarness:
    """Deterministic evaluation harness for real and simulated model backends."""

    def __init__(self, invoker: Any) -> None:
        self.invoker = invoker

    @staticmethod
    def _digest(value: Any) -> str:
        return "sha256:" + sha256(repr(value).encode("utf-8")).hexdigest()

    def evaluate(self, case: EvaluationCase, request: Any) -> EvaluationResult:
        result = self.invoker.invoke(request)
        output = result.output
        checks = {
            "completed": result.status == "completed_on_time",
            "has_output": output is not None,
            "provenance": bool(result.provenance),
        }
        for property_name in case.expected_properties:
            checks[f"expected:{property_name}"] = self._contains_property(output, property_name)
        status = "PASS" if all(checks.values()) else "FAIL"
        provenance = InferenceProvenance(
            invocation_id=result.invocation_id,
            model_id=result.model_id,
            model_version=result.model_version,
            artifact_digest=str(result.provenance.get("artifact_digest", "")),
            runtime=str(result.provenance.get("runtime", "")),
            backend=str(result.provenance.get("backend", "")),
            input_schema_version=getattr(request, "input_schema_version", ""),
            output_schema_version=getattr(request, "output_schema_version", ""),
        )
        return EvaluationResult(
            case_id=case.case_id,
            status=status,
            output_digest=self._digest(output),
            latency_ms=result.latency_ms,
            provenance=provenance,
            checks=checks,
        )

    @staticmethod
    def _contains_property(output: Any, name: str) -> bool:
        if isinstance(output, Mapping):
            return name in output
        return hasattr(output, name)

    @staticmethod
    def serialize(result: EvaluationResult) -> dict[str, Any]:
        return asdict(result)
