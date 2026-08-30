"""Model registry (plan 12, §8 Phase 3 and §9 Phase 4).

The registry is independent of AirLLM. Each model spec records the local alias,
the canonical model ID, and backend artifacts via an explicit mapping layer:

    local alias -> canonical model ID -> backend artifact

Never silently substitute a different checkpoint: backend artifacts must be
resolved explicitly (``resolve_backend_artifact``) and ``qwen3.8:latest`` is
not admitted to the AirLLM pool until its exact artifact identity is recorded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import InferenceConfigurationError, ModelNotFoundError


@dataclass(frozen=True)
class ModelSpec:
    """Registry model specification (plan 12, §8)."""

    id: str  # canonical registry id, e.g. "qwen3.8-27b"
    family: str = ""
    role_candidates: tuple[str, ...] = ()
    backend_preferences: tuple[str, ...] = ()
    source_type: str = "unknown"  # huggingface | ollama | local | unknown
    source_id: str = ""  # e.g. "Qwen/Qwen3.8-27B"
    local_aliases: tuple[str, ...] = ()
    context_limit: int | None = None
    capabilities: dict[str, Any] = field(default_factory=dict)
    hardware_requirements: dict[str, Any] = field(default_factory=dict)
    status: str = "candidate"  # candidate | approved | blocked | retired
    #: backend -> artifact mapping (explicit, never implicit substitution)
    backend_artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: resolved identity facts (§9.5); empty until recorded
    resolved: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "family": self.family,
            "role_candidates": list(self.role_candidates),
            "backend_preferences": list(self.backend_preferences),
            "source_type": self.source_type,
            "source_id": self.source_id,
            "local_aliases": list(self.local_aliases),
            "context_limit": self.context_limit,
            "capabilities": dict(self.capabilities),
            "hardware_requirements": dict(self.hardware_requirements),
            "status": self.status,
            "backend_artifacts": self.backend_artifacts,
            "resolved": dict(self.resolved),
        }

    def resolve_backend_artifact(self, backend_id: str) -> dict[str, Any]:
        """Resolve the backend artifact for ``backend_id``.

        Raises ``InferenceConfigurationError`` when the mapping is missing —
        the registry must never substitute a different checkpoint silently.
        """
        artifact = self.backend_artifacts.get(backend_id)
        if artifact is None:
            raise InferenceConfigurationError(
                f"no backend artifact mapping for model {self.id!r} on backend {backend_id!r}",
                context={"model": self.id, "backend": backend_id},
            )
        return artifact

    def is_airllm_eligible(self) -> bool:
        """A model is AirLLM-eligible only when its artifact identity is resolved."""
        return bool(self.resolved.get("architecture")) and bool(self.resolved.get("parameter_count"))


#: Initial registry contents — exactly the five currently approved aliases
#: (plan 12, §9). No additional model becomes a dependency without a documented
#: adoption decision. AirLLM artifacts are intentionally NOT mapped yet: they
#: must be resolved against the exact Hugging Face checkpoint (Step 17) before
#: eligibility.
def _default_model_specs() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            id="qwen3-4b",
            family="qwen3",
            role_candidates=(
                "lightweight_reasoning",
                "classification",
                "intent_parsing",
                "simple_dialogue",
                "background_summarization",
                "cheap_fallback",
            ),
            backend_preferences=("existing",),
            source_type="ollama",
            source_id="qwen3:4b",
            local_aliases=("qwen3:4b",),
            context_limit=32768,
            capabilities={"text": True, "vision": False, "tool_calling": None, "structured_output": None},
            status="candidate",
        ),
        ModelSpec(
            id="qwen3-8b",
            family="qwen3",
            role_candidates=(
                "default_general_cognition",
                "ordinary_dialogue",
                "lightweight_planning",
                "tool_selection",
                "context_interpretation",
            ),
            backend_preferences=("existing",),
            source_type="ollama",
            source_id="qwen3:8b",
            local_aliases=("qwen3:8b",),
            context_limit=32768,
            capabilities={"text": True, "vision": False, "tool_calling": None, "structured_output": None},
            status="candidate",
        ),
        ModelSpec(
            id="nemotron-3.5-lightning",
            family="nemotron",
            role_candidates=(
                "agentic_planning",
                "long_running_task_orchestration",
                "tool_oriented_reasoning",
                "multi_step_cognitive_work",
            ),
            backend_preferences=("existing",),
            source_type="ollama",
            source_id="nemotron-3.5-lightning:latest",
            local_aliases=("nemotron-3.5-lightning:latest",),
            context_limit=None,
            capabilities={"text": True, "vision": False, "tool_calling": None, "structured_output": None},
            status="candidate",
        ),
        ModelSpec(
            id="qwen3.8-27b",
            family="qwen3.8",
            role_candidates=("deep_reasoning", "multimodal_reasoning"),
            backend_preferences=("airllm", "existing"),
            source_type="huggingface",
            source_id="Qwen/Qwen3.8-27B",
            local_aliases=("qwen3.8:27b",),
            context_limit=None,
            capabilities={"text": True, "vision": True, "tool_calling": None, "structured_output": None},
            hardware_requirements={},
            status="candidate",
            backend_artifacts={},  # resolved only after Step 17 (exact HF artifact)
        ),
        ModelSpec(
            id="qwen3.8-latest",
            family="qwen3.8",
            role_candidates=(),
            backend_preferences=("existing",),
            source_type="ollama",
            source_id="qwen3.8:latest",
            local_aliases=("qwen3.8:latest",),
            context_limit=None,
            capabilities={"text": True, "vision": None, "tool_calling": None, "structured_output": None},
            status="candidate",
            resolved={},  # identity unresolved: never routable until recorded (§9.5)
        ),
    )


class ModelRegistry:
    """Novi-owned, backend-neutral model registry."""

    def __init__(self, specs: tuple[ModelSpec, ...] | None = None) -> None:
        self._specs: dict[str, ModelSpec] = {}
        self._alias_index: dict[str, str] = {}
        for spec in specs or _default_model_specs():
            self.register(spec)

    def register(self, spec: ModelSpec) -> None:
        self._specs[spec.id] = spec
        for alias in spec.local_aliases:
            self._alias_index[alias] = spec.id

    def get(self, model_id: str) -> ModelSpec:
        try:
            return self._specs[model_id]
        except KeyError:
            raise ModelNotFoundError(f"model not found: {model_id}", context={"model": model_id}) from None

    def get_by_alias(self, alias: str) -> ModelSpec:
        canonical = self._alias_index.get(alias)
        if canonical is None:
            raise ModelNotFoundError(f"unknown model alias: {alias}", context={"alias": alias})
        return self.get(canonical)

    def resolve(self, model_hint: str) -> ModelSpec:
        """Resolve a hint that may be an alias or a canonical id."""
        if model_hint in self._specs:
            return self.get(model_hint)
        return self.get_by_alias(model_hint)

    def all(self) -> tuple[ModelSpec, ...]:
        return tuple(self._specs.values())

    def ids(self) -> tuple[str, ...]:
        return tuple(self._specs)

    def routable(self) -> tuple[ModelSpec, ...]:
        """Models the router may select.

        A model is routable only when its status is approved AND (for AirLLM)
        its artifact identity is resolved. ``qwen3.8:latest`` remains unroutable
        until its exact artifact identity/capabilities are recorded (§9.5).
        """
        out = []
        for spec in self._specs.values():
            if spec.status != "approved":
                continue
            if "airllm" in spec.backend_preferences and not spec.is_airllm_eligible():
                continue
            out.append(spec)
        return tuple(out)

    def snapshot(self) -> dict[str, Any]:
        return {"models": [spec.as_dict() for spec in self._specs.values()]}

    # ------------------------------------------------------------- persistence
    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.snapshot(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "ModelRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        specs = tuple(ModelSpec(**item) for item in data["models"])
        return cls(specs)
