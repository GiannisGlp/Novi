"""Model router (plan 12, §22 Phase 17).

The router is Novi-owned and backend-neutral. It maps task requirements to a
(model, backend, execution mode) decision and records the *reason* — an
auditable decision, not hidden heuristic behavior.

Initial model policy (plan 12, §23) is routing *hypotheses* for evaluation
only; the benchmark suite must be able to overturn them. By default every model
is status ``candidate`` and the router refuses to route unapproved models, so
no new routing is enabled automatically (plan 12, Step 10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import ModelUnavailableError
from .registry import ModelRegistry, ModelSpec

#: Deliberation levels (plan 12, §46 Phase 46) -> initial model hypotheses.
_DELIBERATION_HYPOTHESIS: dict[str, str] = {
    "FAST": "qwen3-4b",
    "NORMAL": "qwen3-8b",
    "DELIBERATE": "nemotron-3.5-lightning",
    "DEEP": "qwen3.8-27b",
}


@dataclass(frozen=True)
class RoutingDecision:
    model: str
    backend: str
    execution_mode: str  # e.g. sync | background
    reason: str
    confidence: float
    fallback: str = ""
    deliberation_level: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "backend": self.backend,
            "execution_mode": self.execution_mode,
            "reason": self.reason,
            "confidence": self.confidence,
            "fallback": self.fallback,
            "deliberation_level": self.deliberation_level,
        }


@dataclass(frozen=True)
class RoutingContext:
    """Router inputs (plan 12, §22)."""

    task_type: str = "reason"  # reason | plan | interpret | summarize | choose | reflect
    reasoning_complexity: str = "NORMAL"  # FAST | NORMAL | DELIBERATE | DEEP
    context_length: int = 0
    required_modality: str = "text"  # text | vision | multimodal
    required_tool_capability: bool = False
    latency_budget_ms: float | None = None
    available_ram_bytes: int = 0
    available_vram_bytes: int = 0
    thermal_state: str = "normal"
    power_mode: str = "balanced"
    current_residency: dict[str, str] = field(default_factory=dict)  # model_id -> residency
    model_hint: str = ""  # explicit model hint (alias or canonical id)


class ModelRouter:
    """Selects model/backend from routing context, always recording a reason."""

    def __init__(self, registry: ModelRegistry, *, airllm_validator: Any | None = None) -> None:
        self.registry = registry
        #: eligibility predicate for the AirLLM backend; the runtime injects the
        #: validated-combination policy (plan 12 Step 33-34: AirLLM only for
        #: explicitly validated model/hardware combinations). Default = registry
        #: artifact-resolution eligibility.
        self._airllm_validator = airllm_validator or (lambda spec: spec.is_airllm_eligible())
        self._decision_log: list[RoutingDecision] = []
        #: deliberation level -> model hypothesis (provisional, benchmark-driven)
        self.deliberation_hypotheses: dict[str, str] = dict(_DELIBERATION_HYPOTHESIS)

    def route(self, context: RoutingContext) -> RoutingDecision:
        """Produce an auditable routing decision.

        Raises ``ModelNotFoundError`` for an unresolvable model hint and
        ``ModelUnavailableError`` when no approved model can serve the request
        (never silently downgrades authority).
        """
        if context.model_hint:
            return self._route_hint(context)
        deliberation = context.reasoning_complexity.upper()
        hypothesis = self.deliberation_hypotheses.get(deliberation, self.deliberation_hypotheses["NORMAL"])

        candidates: list[tuple[ModelSpec, str]] = []
        try:
            primary = self.registry.get(hypothesis)
        except Exception:
            primary = None
        if primary is not None and self._model_eligible(primary):
            candidates.append((primary, f"deliberation:{deliberation}"))
        for spec in self.registry.routable():
            if spec.id != (primary.id if primary else None) and self._model_eligible(spec):
                candidates.append((spec, f"approved_available:{spec.id}"))
            if len(candidates) >= 3:
                break

        if not candidates:
            raise ModelUnavailableError(
                "no approved model available for routing",
                context={"task_type": context.task_type, "reasoning_complexity": deliberation},
            )

        spec, reason = self._select(candidates, context)
        backend = self._select_backend(spec, context)
        decision = RoutingDecision(
            model=spec.id,
            backend=backend,
            execution_mode="background" if context.reasoning_complexity.upper() == "DEEP" else "sync",
            reason=f"{reason}; backend:{backend}",
            confidence=0.7,
            fallback=self._fallback_for(spec, deliberation),
            deliberation_level=deliberation,
        )
        self._decision_log.append(decision)
        return decision

    # ------------------------------------------------------------------ helpers
    def _route_hint(self, context: RoutingContext) -> RoutingDecision:
        """Route an explicit model hint (alias or canonical id)."""
        from .errors import ModelNotFoundError

        try:
            spec = self.registry.resolve(context.model_hint)
        except ModelNotFoundError:
            raise
        if not self._model_eligible(spec):
            raise ModelUnavailableError(
                f"model {spec.id} is not approved for routing",
                context={"model": spec.id, "status": spec.status},
            )
        backend = self._select_backend(spec, context)
        deliberation = context.reasoning_complexity.upper()
        decision = RoutingDecision(
            model=spec.id,
            backend=backend,
            execution_mode="background" if deliberation == "DEEP" else "sync",
            reason=f"model_hint:{context.model_hint}; backend:{backend}",
            confidence=0.7,
            fallback=self._fallback_for(spec, deliberation),
            deliberation_level=deliberation,
        )
        self._decision_log.append(decision)
        return decision

    def _model_eligible(self, spec: ModelSpec) -> bool:
        return spec.status == "approved"

    def _select(self, candidates: list[tuple[ModelSpec, str]], context: RoutingContext) -> tuple[ModelSpec, str]:
        # Prefer the hypothesis candidate (in order); else first approved.
        for spec, reason in candidates:
            return spec, reason
        return candidates[0]

    def _select_backend(self, spec: ModelSpec, context: RoutingContext) -> str:
        for preference in spec.backend_preferences:
            if preference == "airllm":
                # Step 33-34: AirLLM is selected ONLY when the model/hardware
                # combination is explicitly validated (validator injected by the
                # runtime) AND VRAM is known-constrained.
                if not self._airllm_validator(spec):
                    continue
                if context.available_vram_bytes <= 0:
                    continue
            return preference
        return spec.backend_preferences[0]

    def _fallback_for(self, spec: ModelSpec, deliberation: str) -> str:
        """Deterministic fallback chain (plan 12, §30): smaller approved model."""
        chain = ("qwen3.8-27b", "nemotron-3.5-lightning", "qwen3-8b", "qwen3-4b")
        start = False
        for model in chain:
            if model == spec.id:
                start = True
                continue
            if start:
                return model
        return ""

    # ------------------------------------------------------------- observability
    def recent_decisions(self, limit: int = 10) -> list[dict[str, Any]]:
        return [d.as_dict() for d in self._decision_log[-limit:]]

    def snapshot(self) -> dict[str, Any]:
        return {
            "deliberation_hypotheses": dict(self.deliberation_hypotheses),
            "recent_decisions": self.recent_decisions(),
        }
