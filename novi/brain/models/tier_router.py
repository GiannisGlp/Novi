"""Model routing tiers (plan 22, Phase 16).

Keep the allowed local models; do not require a large model for every turn.
The router selects by task complexity, latency budget, context size,
uncertainty and required reasoning depth. The model is never the source of
truth for identity / location / world state / memory existence / safety
authorization / physical command validity (plan §20).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FAST = "FAST"            # qwen3:4b — reflex acknowledgements
NORMAL = "NORMAL"        # qwen3:8b — ordinary conversation
COMPLEX = "COMPLEX"      # qwen3.8:27b — grounded reasoning
SPECIALIZED = "SPECIALIZED"  # nemotron-3.5-lightning — latency experiments
EXPERIMENTAL = "EXPERIMENTAL"  # qwen3.8:latest

TIER_MODELS: dict[str, str] = {
    FAST: "qwen3:4b",
    NORMAL: "qwen3:8b",
    COMPLEX: "qwen3.8:27b",
    SPECIALIZED: "nemotron-3.5-lightning:latest",
    EXPERIMENTAL: "qwen3.8:latest",
}

# The model is never the truth source for these (plan §20).
NEVER_MODEL_TRUTH = frozenset({
    "identity", "location", "world_state", "memory_existence",
    "safety_authorization", "physical_command_validity",
})


@dataclass
class RoutingSignals:
    task_complexity: float = 0.0      # 0 trivial .. 1 deep reasoning
    latency_budget_s: float = 30.0    # how long the turn may take
    context_chars: int = 0            # packed context size
    uncertainty: float = 0.0          # 0 certain .. 1 very uncertain
    reasoning_depth: float = 0.0      # 0 reflex .. 1 deliberative


class TierRouter:
    """Deterministic tier selection from cognition signals."""

    def tier_for(self, signals: RoutingSignals) -> str:
        if signals.task_complexity >= 0.8 or signals.reasoning_depth >= 0.8:
            return COMPLEX
        if signals.uncertainty >= 0.7 and signals.task_complexity >= 0.5:
            return COMPLEX
        if signals.task_complexity >= 0.4 or signals.reasoning_depth >= 0.4:
            return NORMAL
        if signals.latency_budget_s <= 5.0 and signals.task_complexity < 0.3:
            return SPECIALIZED
        return FAST

    def model_for(self, signals: RoutingSignals) -> str:
        return TIER_MODELS[self.tier_for(signals)]

    def snapshot(self) -> dict[str, Any]:
        return {"tiers": dict(TIER_MODELS), "never_model_truth": sorted(NEVER_MODEL_TRUTH)}
