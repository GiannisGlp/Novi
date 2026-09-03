"""Cognitive Failure-Mode Handling for the Mac Brain.

Defines expected failures of cognition and the required safe behavior.
When required safety information is unavailable, the system fails to the
safest useful state rather than guessing.

Canonical authority: docs/03-cognition/16_COGNITIVE_FAILURE_MODES.md

Failure categories:
  perception_uncertainty, identity_ambiguity, knowledge_conflict,
  model_hallucination, context_failure, tool_failure, resource_exhaustion,
  contradictory_world_state, model_unavailable, corrupted_data.

Degraded modes:
  perception_degraded, identity_degraded, reasoning_degraded,
  memory_degraded, network_offline, compute_constrained, safety_only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

# ---------------------------------------------------------------------------
# Failure categories (docs/03-cognition/16)
# ---------------------------------------------------------------------------

PERCEPTION_UNCERTAINTY = "perception_uncertainty"
IDENTITY_AMBIGUITY = "identity_ambiguity"
KNOWLEDGE_CONFLICT = "knowledge_conflict"
MODEL_HALLUCINATION = "model_hallucination"
CONTEXT_FAILURE = "context_failure"
TOOL_FAILURE = "tool_failure"
RESOURCE_EXHAUSTION = "resource_exhaustion"
CONTRADICTORY_WORLD_STATE = "contradictory_world_state"
MODEL_UNAVAILABLE = "model_unavailable"
CORRUPTED_DATA = "corrupted_data"

ALL_FAILURE_CATEGORIES = frozenset({
    PERCEPTION_UNCERTAINTY, IDENTITY_AMBIGUITY, KNOWLEDGE_CONFLICT,
    MODEL_HALLUCINATION, CONTEXT_FAILURE, TOOL_FAILURE, RESOURCE_EXHAUSTION,
    CONTRADICTORY_WORLD_STATE, MODEL_UNAVAILABLE, CORRUPTED_DATA,
})


# ---------------------------------------------------------------------------
# Degraded modes (docs/03-cognition/16 §Degraded Modes)
# ---------------------------------------------------------------------------

class DegradedMode(str, Enum):
    NORMAL = "normal"  # no degradation
    PERCEPTION_DEGRADED = "perception_degraded"
    IDENTITY_DEGRADED = "identity_degraded"
    REASONING_DEGRADED = "reasoning_degraded"
    MEMORY_DEGRADED = "memory_degraded"
    NETWORK_OFFLINE = "network_offline"
    COMPUTE_CONSTRAINED = "compute_constrained"
    SAFETY_ONLY = "safety_only"


# ---------------------------------------------------------------------------
# Failure record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FailureRecord:
    """A detected cognitive failure with its category, severity, and fallback."""
    failure_id: str
    category: str  # one of ALL_FAILURE_CATEGORIES
    severity: str  # info | warning | error | critical
    component: str  # perception | identity | memory | reasoning | context | tool | world_model
    message: str
    fallback_action: str  # what the system did instead
    degraded_mode: str  # what degraded mode was entered (if any)
    timestamp: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "category": self.category,
            "severity": self.severity,
            "component": self.component,
            "message": self.message,
            "fallback_action": self.fallback_action,
            "degraded_mode": self.degraded_mode,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# FailureHandler — detects failures and manages degraded modes
# ---------------------------------------------------------------------------

#: Maximum retained failure records. Readers only ever use the last 20
#: (``recent_failures``) plus category filters over the recent window, so a
#: bounded tail preserves every consumer while capping per-cycle growth
#: (plan 02, Rule 1/Rule 3).
MAX_FAILURE_RECORDS = 512


class FailureHandler:
    """Detects cognitive failures and manages graceful degradation.

    When a failure is detected, the handler:
      1. Records the failure with category, severity, and fallback action.
      2. Transitions to the appropriate degraded mode.
      3. Emits a failure event for observability.
      4. Provides fallback behavior guidance.

    The handler maintains the current degraded mode and can detect when
    conditions improve to return to normal operation.

    Improvements over the initial implementation:
      - Configurable recovery thresholds per severity (not a single count).
      - Recovery can be gated by a condition_check callable to verify the
        failure condition is actually resolved, not just count attempts.
      - Component-level degradation tracking: multiple components can be
        degraded simultaneously, and recovery is keyed to the most restrictive
        still-degraded component rather than the most recent failure.
    """

    # Map failure categories to degraded modes.
    _CATEGORY_TO_MODE: dict[str, DegradedMode] = {
        PERCEPTION_UNCERTAINTY: DegradedMode.PERCEPTION_DEGRADED,
        IDENTITY_AMBIGUITY: DegradedMode.IDENTITY_DEGRADED,
        MODEL_HALLUCINATION: DegradedMode.REASONING_DEGRADED,
        CONTEXT_FAILURE: DegradedMode.REASONING_DEGRADED,
        MODEL_UNAVAILABLE: DegradedMode.REASONING_DEGRADED,
        TOOL_FAILURE: DegradedMode.REASONING_DEGRADED,
        RESOURCE_EXHAUSTION: DegradedMode.COMPUTE_CONSTRAINED,
        CONTRADICTORY_WORLD_STATE: DegradedMode.PERCEPTION_DEGRADED,
        CORRUPTED_DATA: DegradedMode.MEMORY_DEGRADED,
        KNOWLEDGE_CONFLICT: DegradedMode.REASONING_DEGRADED,
    }

    # Map failure categories to fallback actions.
    _CATEGORY_TO_FALLBACK: dict[str, str] = {
        PERCEPTION_UNCERTAINTY: "preserve_ambiguity_seek_evidence",
        IDENTITY_AMBIGUITY: "avoid_sensitive_personalization",
        KNOWLEDGE_CONFLICT: "retain_both_claims_lower_confidence",
        MODEL_HALLUCINATION: "require_retrieval_evidence",
        CONTEXT_FAILURE: "retrieve_again_or_defer",
        TOOL_FAILURE: "return_structured_failure_use_fallback",
        RESOURCE_EXHAUSTION: "degrade_non_critical_preserve_safety",
        CONTRADICTORY_WORLD_STATE: "maintain_competing_hypotheses",
        MODEL_UNAVAILABLE: "use_deterministic_fallback",
        CORRUPTED_DATA: "isolate_affected_records",
    }

    # Recovery thresholds per severity level.
    _RECOVERY_THRESHOLDS: dict[str, int] = {
        "info": 1,       # info-level failures recover quickly
        "warning": 3,    # warning: 3 cycles of clear perception
        "error": 5,      # error: 5 cycles before attempting recovery
        "critical": 10,  # critical: requires sustained normal operation
    }

    def __init__(
        self,
        *,
        recovery_thresholds: dict[str, int] | None = None,
    ) -> None:
        self._failures: list[FailureRecord] = []
        self._degraded_mode: DegradedMode = DegradedMode.NORMAL
        self._degraded_since: str = ""
        self._recovery_attempts: int = 0
        self._recovery_thresholds = recovery_thresholds or dict(self._RECOVERY_THRESHOLDS)
        # Track which components are degraded.
        self._degraded_components: set[str] = set()
        # Per-component degraded mode, so the overall mode is recomputed from
        # the most restrictive currently-degraded component (not overwritten by
        # the most recent failure).
        self._component_modes: dict[str, DegradedMode] = {}
        # Per-component recovery threshold, so recovery is keyed to the most
        # severe still-degraded component rather than the most recent failure.
        self._component_threshold: dict[str, int] = {}

    @property
    def degraded_mode(self) -> DegradedMode:
        return self._degraded_mode

    @property
    def is_degraded(self) -> bool:
        return self._degraded_mode != DegradedMode.NORMAL

    @property
    def is_safety_only(self) -> bool:
        return self._degraded_mode == DegradedMode.SAFETY_ONLY

    @property
    def degraded_components(self) -> frozenset[str]:
        """Components that are currently degraded."""
        return frozenset(self._degraded_components)

    def report_failure(
        self,
        category: str,
        *,
        severity: str = "warning",
        component: str = "unknown",
        message: str = "",
        timestamp: str = "",
    ) -> FailureRecord:
        """Report a cognitive failure and transition to the appropriate degraded mode.

        Returns the FailureRecord for observability.
        """
        if category not in ALL_FAILURE_CATEGORIES:
            raise ValueError(f"unknown failure category: {category!r}")

        fallback = self._CATEGORY_TO_FALLBACK.get(category, "fail_safe")
        new_mode = self._CATEGORY_TO_MODE.get(category, DegradedMode.SAFETY_ONLY)

        # Escalate to safety_only for critical severity.
        if severity == "critical":
            new_mode = DegradedMode.SAFETY_ONLY

        # Track the degraded component and its mode, then recompute the overall
        # mode as the most restrictive among all currently-degraded components.
        self._degraded_components.add(component)
        self._component_modes[component] = new_mode
        self._component_threshold[component] = self._recovery_thresholds.get(severity, 3)
        self._degraded_mode = self._most_restrictive()
        if self._degraded_mode != DegradedMode.NORMAL and not self._degraded_since:
            self._degraded_since = timestamp

        # Reset global recovery counter (new failure occurred).
        self._recovery_attempts = 0

        record = FailureRecord(
            failure_id=str(uuid4()),
            category=category,
            severity=severity,
            component=component,
            message=message,
            fallback_action=fallback,
            degraded_mode=self._degraded_mode.value,
            timestamp=timestamp,
        )
        self._failures.append(record)
        if len(self._failures) > MAX_FAILURE_RECORDS:
            del self._failures[: len(self._failures) - MAX_FAILURE_RECORDS]
        return record

    def _most_restrictive(self) -> DegradedMode:
        """The most restrictive mode among currently-degraded components."""
        mode_order = {
            DegradedMode.NORMAL: 0,
            DegradedMode.PERCEPTION_DEGRADED: 1,
            DegradedMode.IDENTITY_DEGRADED: 1,
            DegradedMode.MEMORY_DEGRADED: 2,
            DegradedMode.REASONING_DEGRADED: 2,
            DegradedMode.NETWORK_OFFLINE: 2,
            DegradedMode.COMPUTE_CONSTRAINED: 3,
            DegradedMode.SAFETY_ONLY: 4,
        }
        if not self._component_modes:
            return DegradedMode.NORMAL
        return max(self._component_modes.values(), key=lambda m: mode_order.get(m, 0))

    def attempt_recovery(
        self,
        *,
        condition_check: Callable[[], bool] | None = None,
    ) -> bool:
        """Attempt to recover from degraded mode.

        Args:
            condition_check: Optional callable that returns True if the failure
                             condition is actually resolved. If provided and
                             returns False, recovery is not attempted even if
                             the threshold is met.

        Returns True if recovery was successful (back to NORMAL).
        """
        if self._degraded_mode == DegradedMode.NORMAL:
            return True

        self._recovery_attempts += 1

        # Determine the threshold based on the most restrictive still-degraded
        # component (not the most recent failure, so a critical condition is not
        # cleared just because a milder failure followed it).
        threshold = max(self._component_threshold.values()) if self._component_threshold else 3

        if self._recovery_attempts < threshold:
            return False

        # If a condition check is provided, verify the failure is actually resolved.
        if condition_check is not None and not condition_check():
            return False

        # Recovery successful.
        self._degraded_mode = DegradedMode.NORMAL
        self._degraded_since = ""
        self._recovery_attempts = 0
        self._degraded_components.clear()
        self._component_modes.clear()
        self._component_threshold.clear()
        return True

    def clear_component(self, component: str) -> None:
        """Mark a component as recovered (no longer degraded)."""
        self._degraded_components.discard(component)
        self._component_modes.pop(component, None)
        self._component_threshold.pop(component, None)
        # Recompute the overall mode from the remaining degraded components.
        self._degraded_mode = self._most_restrictive()
        if self._degraded_mode == DegradedMode.NORMAL:
            self._degraded_since = ""
            self._recovery_attempts = 0

    def reset_recovery(self) -> None:
        """Reset recovery attempts (e.g. when a new failure occurs)."""
        self._recovery_attempts = 0

    @property
    def failure_count(self) -> int:
        return len(self._failures)

    @property
    def recent_failures(self) -> tuple[FailureRecord, ...]:
        """Last 20 failures."""
        return tuple(self._failures[-20:])

    def failures_by_category(self, category: str) -> tuple[FailureRecord, ...]:
        return tuple(f for f in self._failures if f.category == category)

    def failures_by_component(self, component: str) -> tuple[FailureRecord, ...]:
        return tuple(f for f in self._failures if f.component == component)

    def snapshot(self) -> dict[str, Any]:
        return {
            "degraded_mode": self._degraded_mode.value,
            "is_degraded": self.is_degraded,
            "is_safety_only": self.is_safety_only,
            "degraded_since": self._degraded_since,
            "degraded_components": list(self._degraded_components),
            "failure_count": self.failure_count,
            "recovery_attempts": self._recovery_attempts,
            "recovery_threshold": self._recovery_thresholds.get(
                (self._failures[-1].severity if self._failures else "warning"), 3
            ),
            "recent_failures": [f.snapshot() for f in self.recent_failures],
        }
