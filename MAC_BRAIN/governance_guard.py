"""Governance Guard for the Mac Brain (PERFECTING_PLAN Step 3).

A runtime guard between proposal and execution. Models never command action;
even deterministic actions pass through the governance guard.

Canonical authority:
  - docs/02-autonomy/09_AUTONOMY_SAFETY_BOUNDARIES.md
  - PERFECTING_PLAN/04_GAP_ANALYSIS_AUTONOMY.md

The governance guard implements the policy pipeline:
  model proposal → schema validation → identity/authorization → risk
  classification → policy evaluation → physical/environment checks → safety gate
  → execution

Key invariants:
  - No action executes without a governance grant.
  - The model cannot override governance outcomes (deny, modify, require
    confirmation, pause, stop, enter safe degraded mode).
  - When required safety information is unavailable, fail to the safest useful
    state rather than guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

# ---------------------------------------------------------------------------
# Governance decisions
# ---------------------------------------------------------------------------

ALLOW = "ALLOW"
DENY = "DENY"
MODIFY = "MODIFY"       # modify parameters within safe bounds
REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
PAUSE = "PAUSE"
STOP = "STOP"
DEGRADED_MODE = "DEGRADED_MODE"

ALL_GOVERNANCE_DECISIONS = frozenset({
    ALLOW, DENY, MODIFY, REQUIRE_CONFIRMATION, PAUSE, STOP, DEGRADED_MODE,
})


@dataclass(frozen=True)
class ActionProposal:
    """A proposed action from the autonomy/planning layer."""
    proposal_id: str
    action: str
    parameters: dict[str, Any]
    risk_class: str = "R0"
    actor: str = "system"
    source: str = "deterministic"  # deterministic | model | user
    rationale: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "action": self.action,
            "parameters": dict(self.parameters),
            "risk_class": self.risk_class,
            "actor": self.actor,
            "source": self.source,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class GovernanceGrant:
    """A governance decision for a proposed action."""
    grant_id: str
    proposal_id: str
    decision: str  # ALLOW | DENY | MODIFY | REQUIRE_CONFIRMATION | PAUSE | STOP | DEGRADED_MODE
    reason: str = ""
    modified_parameters: dict[str, Any] | None = None
    conditions: tuple[str, ...] = ()

    @property
    def is_allowed(self) -> bool:
        return self.decision == ALLOW

    @property
    def is_denied(self) -> bool:
        return self.decision == DENY

    def snapshot(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "proposal_id": self.proposal_id,
            "decision": self.decision,
            "reason": self.reason,
            "modified_parameters": self.modified_parameters,
            "conditions": list(self.conditions),
        }


# ---------------------------------------------------------------------------
# GovernanceGuard
# ---------------------------------------------------------------------------

# Actions that are always safe to execute without confirmation (R0/R1).
_ALWAYS_SAFE_ACTIONS = frozenset({"wait", "observe", "stop", "idle", "speak"})

# Actions that require confirmation (R3+).
_REQUIRES_CONFIRMATION_ACTIONS = frozenset({"pick", "navigate", "move_forward", "turn_left", "turn_right"})

# Actions that are prohibited in degraded mode.
_PROHIBITED_IN_DEGRADED = frozenset({"navigate", "move_forward", "pick", "turn_left", "turn_right"})


class GovernanceGuard:
    """The runtime governance guard between proposal and execution.

    Every proposed action must pass through this guard before execution.
    The model cannot override governance outcomes.
    """

    def __init__(
        self,
        *,
        degraded_mode: bool = False,
        require_confirmation_above: str = "R3",
        safe_actions: set[str] | None = None,
    ) -> None:
        self.degraded_mode = degraded_mode
        self._risk_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}
        self.require_confirmation_above = require_confirmation_above
        self._safe_actions = safe_actions or _ALWAYS_SAFE_ACTIONS
        self._grants: dict[str, GovernanceGrant] = {}
        self._denied_count = 0
        self._allowed_count = 0

    def evaluate(self, proposal: ActionProposal) -> GovernanceGrant:
        """Evaluate a proposed action and return a governance grant.

        The grant must be ALLOW for the action to execute.
        """
        grant_id = str(uuid4())

        # Stage 1: Degraded mode check — some actions are prohibited.
        if self.degraded_mode and proposal.action in _PROHIBITED_IN_DEGRADED:
            grant = GovernanceGrant(
                grant_id=grant_id, proposal_id=proposal.proposal_id,
                decision=DEGRADED_MODE,
                reason=f"action {proposal.action!r} prohibited in degraded mode",
            )
            self._grants[grant_id] = grant
            return grant

        # Stage 2: Risk classification — R5 is always denied.
        if proposal.risk_class == "R5":
            grant = GovernanceGrant(
                grant_id=grant_id, proposal_id=proposal.proposal_id,
                decision=DENY, reason="R5_action_requires_external_safety_authority",
            )
            self._grants[grant_id] = grant
            self._denied_count += 1
            return grant

        # Stage 3: Model-source actions at R4+ require confirmation.
        if proposal.source == "model" and self._risk_order.get(proposal.risk_class, 0) >= self._risk_order.get("R4", 4):
            grant = GovernanceGrant(
                grant_id=grant_id, proposal_id=proposal.proposal_id,
                decision=REQUIRE_CONFIRMATION,
                reason=f"model_proposed_{proposal.risk_class}_action_requires_confirmation",
            )
            self._grants[grant_id] = grant
            return grant

        # Stage 4: R3+ actions require confirmation.
        if self._risk_order.get(proposal.risk_class, 0) >= self._risk_order.get(self.require_confirmation_above, 3):
            if proposal.action in _REQUIRES_CONFIRMATION_ACTIONS and proposal.source != "user":
                grant = GovernanceGrant(
                    grant_id=grant_id, proposal_id=proposal.proposal_id,
                    decision=REQUIRE_CONFIRMATION,
                    reason=f"{proposal.risk_class}_action_requires_confirmation",
                )
                self._grants[grant_id] = grant
                return grant

        # Stage 5: Always-safe actions pass.
        if proposal.action in self._safe_actions and proposal.risk_class in ("R0", "R1"):
            grant = GovernanceGrant(
                grant_id=grant_id, proposal_id=proposal.proposal_id,
                decision=ALLOW, reason="safe_action",
            )
            self._grants[grant_id] = grant
            self._allowed_count += 1
            return grant

        # Stage 6: Default — allow R0/R1, deny unknown high-risk.
        if proposal.risk_class in ("R0", "R1"):
            grant = GovernanceGrant(
                grant_id=grant_id, proposal_id=proposal.proposal_id,
                decision=ALLOW, reason="low_risk_allowed",
            )
            self._grants[grant_id] = grant
            self._allowed_count += 1
            return grant

        # Stage 7: R2+ without explicit confirmation → require confirmation.
        grant = GovernanceGrant(
            grant_id=grant_id, proposal_id=proposal.proposal_id,
            decision=REQUIRE_CONFIRMATION,
            reason=f"{proposal.risk_class}_action_requires_confirmation",
        )
        self._grants[grant_id] = grant
        return grant

    def confirm(self, grant_id: str) -> GovernanceGrant | None:
        """Confirm a previously REQUIRE_CONFIRMATION grant."""
        grant = self._grants.get(grant_id)
        if grant is None or grant.decision != REQUIRE_CONFIRMATION:
            return None
        confirmed = GovernanceGrant(
            grant_id=grant_id, proposal_id=grant.proposal_id,
            decision=ALLOW, reason="confirmed_by_user_or_operator",
            conditions=grant.conditions,
        )
        self._grants[grant_id] = confirmed
        self._allowed_count += 1
        return confirmed

    def set_degraded_mode(self, degraded: bool) -> None:
        self.degraded_mode = degraded

    @property
    def allowed_count(self) -> int:
        return self._allowed_count

    @property
    def denied_count(self) -> int:
        return self._denied_count

    def get_grant(self, grant_id: str) -> GovernanceGrant | None:
        return self._grants.get(grant_id)

    def all_grants(self) -> tuple[GovernanceGrant, ...]:
        return tuple(self._grants.values())
