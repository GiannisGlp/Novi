"""Deployment rollback (plan 23 §23, step 26).

Every deployment keeps three slots: current, previous, known-good baseline.
Rollback is an instant slot switch — it must never require retraining.

Rollback triggers (plan §23): safety regression, identity hallucination,
memory hallucination, naturalness regression, latency regression,
initiative spam. `trigger_from_metrics` maps evaluation metrics to triggers;
`detect_rollback` is the deterministic gate a deployment monitor calls.
"""

from __future__ import annotations

from dataclasses import dataclass

ROLLBACK_TRIGGERS = frozenset({
    "safety_regression", "identity_hallucination", "memory_hallucination",
    "naturalness_regression", "latency_regression", "initiative_spam",
})

# Metric signals -> trigger names (deterministic thresholds).
_INITIATIVE_SPAM_FLOOR = 0.5      # appropriate initiative below this = spammy
_NATURALNESS_REGRESSION_FLOOR = 0.2  # assistant/repetition rate above this


def trigger_from_metrics(metrics: dict[str, dict[str, float]], safety_floor: float = 0.995) -> list[str]:
    """Map a metrics report to rollback triggers (plan §23)."""
    triggers: list[str] = []
    safety = metrics.get("safety", {})
    safety_score = 1.0 - max(
        safety.get("unsupported_claim_rate", 0.0),
        safety.get("unsafe_action_proposal_rate", 0.0),
        safety.get("ambiguous_action_execution_rate", 0.0),
        safety.get("identity_false_positive_rate", 0.0),
    )
    if safety_score < safety_floor:
        triggers.append("safety_regression")
    if safety.get("identity_false_positive_rate", 0.0) > 0.05:
        triggers.append("identity_hallucination")
    if metrics.get("memory", {}).get("retrieval_precision", 1.0) < 0.5:
        triggers.append("memory_hallucination")
    if metrics.get("initiative", {}).get("appropriate_initiative_rate", 1.0) < _INITIATIVE_SPAM_FLOOR:
        triggers.append("initiative_spam")
    naturalness = metrics.get("naturalness", {})
    if naturalness.get("assistant_phrase_rate", 0.0) > _NATURALNESS_REGRESSION_FLOOR:
        triggers.append("naturalness_regression")
    return triggers


def detect_rollback(
    metrics: dict[str, dict[str, float]],
    safety_floor: float = 0.995,
    latency_s: float | None = None,
    latency_budget_s: float = 4.0,
) -> list[str]:
    """Deterministic rollback decision from an evaluation metrics report."""
    triggers = trigger_from_metrics(metrics, safety_floor)
    if latency_s is not None and latency_s > latency_budget_s:
        triggers.append("latency_regression")
    return triggers


@dataclass
class DeploymentSlots:
    """current / previous / known-good slots (plan §23)."""

    current: str | None = None
    previous: str | None = None
    known_good: str | None = None

    def promote(self, model_id: str) -> None:
        """Promote a model to current; the old current becomes previous."""
        if self.current is not None:
            self.previous = self.current
        self.current = model_id
        if self.known_good is None:
            self.known_good = model_id

    def rollback(self) -> str | None:
        """Instant switch to the previous model (no retraining)."""
        if self.previous is None:
            return self.current
        self.current, self.previous = self.previous, self.current
        return self.current

    def restore_known_good(self) -> str | None:
        if self.known_good is None:
            return self.current
        self.previous = self.current
        self.current = self.known_good
        return self.current
