from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class PerceptionCase:
    case_id: str
    modality: str
    expected_labels: tuple[str, ...] = ()
    minimum_confidence: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PerceptionEvaluation:
    case_id: str
    passed: bool
    latency_ms: float
    detected_labels: tuple[str, ...]
    confidence: float
    failure_reasons: tuple[str, ...] = ()


class PerceptionBackend(Protocol):
    def infer(self, case: PerceptionCase) -> Mapping[str, Any]: ...


class DeterministicPerceptionBackend:
    """CI backend for contract evaluation; no learned inference is performed."""

    def infer(self, case: PerceptionCase) -> Mapping[str, Any]:
        return {
            "labels": list(case.expected_labels),
            "confidence": 1.0,
            "latency_ms": 1.0,
        }


class PerceptionEvaluator:
    """Hardware/model-neutral evaluator for specialist perception models."""

    def __init__(self, backend: PerceptionBackend | None = None) -> None:
        self.backend = backend or DeterministicPerceptionBackend()

    def evaluate(self, case: PerceptionCase) -> PerceptionEvaluation:
        result = self.backend.infer(case)
        labels = tuple(str(label) for label in result.get("labels", ()))
        confidence = float(result.get("confidence", 0.0))
        latency_ms = float(result.get("latency_ms", 0.0))
        failures: list[str] = []

        missing = sorted(set(case.expected_labels) - set(labels))
        if missing:
            failures.append(f"missing_labels:{','.join(missing)}")
        if confidence < case.minimum_confidence:
            failures.append("confidence_below_threshold")
        if latency_ms < 0:
            failures.append("invalid_latency")

        return PerceptionEvaluation(
            case_id=case.case_id,
            passed=not failures,
            latency_ms=latency_ms,
            detected_labels=labels,
            confidence=confidence,
            failure_reasons=tuple(failures),
        )
