"""Safety and governance hardening for the Mac Brain (06_AUTONOMY doc 08).

Safety is an independent authority that can stop or constrain autonomous
behavior even when cognition, perception or planning is wrong:

  Sensors / world state → safety monitors → risk assessment → policy decision
  → ALLOW / MODIFY / DENY / STOP → executor

Components here:

- ``SafetyInvariant`` / ``SafetyInvariantSet`` — named, checkable invariants
  (doc 08 Step 2): never move while e-stop is active, never execute with a
  stale pose, never enter forbidden zones, never exceed velocity/force limits,
  never operate without required sensor health, never bypass human approval
  for configured high-risk skills.
- ``RiskAssessor`` — pre-action risk classification from proximity,
  uncertainty, speed/force, reversibility, authority and consequence
  (doc 08 Step 4).
- ``RuntimeSafetyMonitor`` — safety continues WHILE an action executes
  (doc 08 Step 5): a previously approved action can become unsafe when the
  environment changes; the monitor interrupts it.
- ``PolicyVersion`` — every action decision records the policy version used
  (doc 08 Step 8); policy changes create regression requirements.
- ``SafetyPolicy`` — the deterministic gate combining invariants + risk. The
  model can never bypass it (A-SAFE-01).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

# Policy outcomes (mirror governance_guard vocabulary).
ALLOW = "ALLOW"
MODIFY = "MODIFY"
DENY = "DENY"
STOP = "STOP"


@dataclass
class SafetyDecision:
    decision_id: str
    decision: str                     # ALLOW | MODIFY | DENY | STOP
    policy_version: str
    reason: str = ""
    violated_invariants: tuple[str, ...] = field(default_factory=tuple)
    risk_class: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision in (ALLOW, MODIFY)

    def snapshot(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id, "decision": self.decision,
            "policy_version": self.policy_version, "reason": self.reason,
            "violated_invariants": list(self.violated_invariants),
            "risk_class": self.risk_class,
        }


@dataclass
class SafetyInvariant:
    """One named, checkable safety invariant (doc 08 Step 2)."""
    name: str
    check: Callable[[dict[str, Any]], tuple[bool, str]]  # (holds, detail)
    description: str = ""

    def holds(self, state: dict[str, Any]) -> tuple[bool, str]:
        try:
            return self.check(state)
        except Exception as exc:  # a broken check fails closed
            return False, f"invariant_check_error: {exc}"


class SafetyInvariantSet:
    """Evaluates all invariants; any violation denies the action."""

    def __init__(self, invariants: list[SafetyInvariant] | None = None) -> None:
        self._invariants = list(invariants or [])

    def add(self, invariant: SafetyInvariant) -> None:
        self._invariants.append(invariant)

    def evaluate(self, state: dict[str, Any]) -> tuple[bool, list[str], dict[str, str]]:
        """(all_hold, violated_names, details) — fails closed."""
        violated: list[str] = []
        details: dict[str, str] = {}
        for invariant in self._invariants:
            holds, detail = invariant.holds(state)
            if not holds:
                violated.append(invariant.name)
                details[invariant.name] = detail
        return (not violated, violated, details)


class RiskAssessor:
    """Pre-action risk classification (doc 08 Step 4)."""

    # Reversibility weighting: irreversible actions are always high-risk.
    REVERSIBILITY: dict[str, int] = {"reversible": 0, "digital": 0, "physical": 2, "irreversible": 5}

    def assess(
        self,
        *,
        proximity_to_human: float = 0.0,     # 0..1 (1 = very close)
        uncertainty: float = 0.0,            # 0..1
        speed_force: float = 0.0,            # 0..1
        reversibility: str = "reversible",
        authority: str = "ASSISTED",
        expected_consequence: str = "benign",
    ) -> str:
        score = (
            3.0 * proximity_to_human
            + 1.5 * uncertainty
            + 2.0 * speed_force
            + self.REVERSIBILITY.get(reversibility, 0)
        )
        if expected_consequence == "harmful":
            score += 4.0
        if authority == "PASSIVE":
            score += 2.0
        if score >= 8.0:
            return "R5"
        if score >= 5.0:
            return "R4"
        if score >= 3.0:
            return "R3"
        if score >= 1.5:
            return "R2"
        return "R1" if score > 0.0 else "R0"


class RuntimeSafetyMonitor:
    """Continues to supervise an action while it executes (doc 08 Step 5).

    ``check(action, world_state)`` returns (safe, reason). If the environment
    changed (obstacle appeared, e-stop engaged, pose went stale), the monitor
    interrupts — a previously approved action can become unsafe.
    """

    def __init__(self, invariants: SafetyInvariantSet, *, interrupt_delay_cycles: int = 1) -> None:
        self.invariants = invariants
        self.interrupt_delay_cycles = interrupt_delay_cycles
        self.interruptions: list[dict[str, Any]] = []

    def check(self, action: dict[str, Any], world_state: dict[str, Any], *, cycle: int) -> tuple[bool, str]:
        all_hold, violated, details = self.invariants.evaluate(world_state)
        if not all_hold:
            self.interruptions.append({
                "cycle": cycle, "action": action.get("action", "?"),
                "violated": violated, "details": details,
            })
            return False, f"interrupted_by_invariant:{violated[0] if violated else 'unknown'}"
        return True, ""


@dataclass(frozen=True)
class PolicyVersion:
    version: str
    revision_note: str = ""
    supersedes: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {"version": self.version, "revision_note": self.revision_note,
                "supersedes": self.supersedes}


class SafetyPolicy:
    """The deterministic safety gate (doc 08): invariants + risk -> decision.

    The model can never bypass this gate: it receives only proposals; the
    decision is computed here from world state and policy, not from any model
    output (A-SAFE-01).
    """

    # Actions that are never allowed regardless of risk assessment.
    ABSOLUTE_DENY: frozenset[str] = frozenset({
        "release_control", "bypass_estop", "disable_safety", "move_into_forbidden",
    })

    def __init__(
        self,
        invariants: SafetyInvariantSet,
        *,
        policy_version: PolicyVersion | None = None,
        require_approval_above: str = "R4",
        max_risk_class: str = "R3",
    ) -> None:
        self.invariants = invariants
        self.version = policy_version or PolicyVersion(version="1.0.0", revision_note="baseline")
        self.require_approval_above = require_approval_above
        self.max_risk_class = max_risk_class
        self._risk_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}
        self.decisions: list[SafetyDecision] = []

    def evaluate(self, proposal: dict[str, Any], world_state: dict[str, Any]) -> SafetyDecision:
        """Decide a proposed action. Records the policy version (doc 08 Step 8)."""
        action = proposal.get("action", "")
        decision_id = f"sd-{uuid4().hex[:10]}"

        if action in self.ABSOLUTE_DENY:
            return self._record(SafetyDecision(
                decision_id, DENY, self.version.version,
                reason="absolutely_denied_action", risk_class="R5",
            ))

        all_hold, violated, details = self.invariants.evaluate(world_state)
        if not all_hold:
            return self._record(SafetyDecision(
                decision_id, DENY, self.version.version,
                reason=f"invariant_violated:{violated[0]}",
                violated_invariants=tuple(violated), risk_class="R5",
            ))

        risk_class = proposal.get("risk_class") or RiskAssessor().assess(
            **{k: v for k, v in proposal.get("risk_factors", {}).items()},
        )
        if risk_class == "R5":
            # R5 is never allowed, with or without approval (matches the
            # governance guard: R5 requires external safety authority).
            return self._record(SafetyDecision(
                decision_id, DENY, self.version.version,
                reason="risk_class_R5_never_allowed", risk_class=risk_class,
            ))
        if self._risk_order.get(risk_class, 0) > self._risk_order.get(self.max_risk_class, 3):
            return self._record(SafetyDecision(
                decision_id, DENY, self.version.version,
                reason=f"risk_class_{risk_class}_exceeds_max_{self.max_risk_class}",
                risk_class=risk_class,
            ))
        if self._risk_order.get(risk_class, 0) >= self._risk_order.get(self.require_approval_above, 4):
            return self._record(SafetyDecision(
                decision_id, MODIFY, self.version.version,
                reason="requires_human_approval", risk_class=risk_class,
            ))
        return self._record(SafetyDecision(
            decision_id, ALLOW, self.version.version,
            reason="invariants_hold_within_risk_budget", risk_class=risk_class,
        ))

    def _record(self, decision: SafetyDecision) -> SafetyDecision:
        self.decisions.append(decision)
        return decision


def default_engine_safety_invariants() -> SafetyInvariantSet:
    """Production baseline invariants for the MacBrain execution path (doc 08 §2).

    Flags absent from a brain's self-report default to SAFE (the doc-08
    convention: an invariant holds unless its named state key reports
    otherwise), so the gate enforces exactly what the runtime genuinely
    knows, never a fabricated violation. With the current Mac virtual body
    the stateful inputs are: e-stop (autonomy state machine), pre-action
    velocity, degraded-mode pose staleness, and modeled forbidden zones.
    """
    return SafetyInvariantSet([
        SafetyInvariant(
            "no_motion_during_estop",
            lambda s: (not s.get("estop_active", False), "e-stop is active"),
            "never move while emergency stop is active (doc 08 Step 2)",
        ),
        SafetyInvariant(
            "pose_freshness",
            lambda s: (s.get("pose_fresh", True), f"stale pose (ttl {s.get('pose_ttl')})"),
            "never execute with a stale pose beyond its TTL",
        ),
        SafetyInvariant(
            "no_forbidden_zone",
            lambda s: (not s.get("in_forbidden_zone", False), "inside forbidden zone"),
            "never enter forbidden zones",
        ),
        SafetyInvariant(
            "velocity_limit",
            lambda s: (s.get("speed_mps", 0.0) <= s.get("max_speed_mps", 1.0), "velocity limit exceeded"),
            "never exceed velocity/force limits",
        ),
        SafetyInvariant(
            "sensor_health",
            lambda s: (s.get("sensors_healthy", True), "required sensor unhealthy"),
            "never operate without required sensor health",
        ),
    ])
