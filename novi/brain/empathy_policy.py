"""Empathy policy (plan 24, Phase 10).

Empathy is represented as a *behavioral strategy*, not a claim about private
feelings. The policy selects one or more strategies based on observable
evidence (plan §14):

  - frustration + Novi caused problem → ACKNOWLEDGE + APOLOGIZE + SOLVE
  - frustration + Novi did not cause → ACKNOWLEDGE + SOLVE
  - disengagement → GIVE_SPACE
  - success → CELEBRATE, proportionally

Deterministic and hardware-free: a pure function of the evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STRATEGIES = (
    "ACKNOWLEDGE",
    "VALIDATE",
    "CLARIFY",
    "SUPPORT",
    "SOLVE",
    "ENCOURAGE",
    "GIVE_SPACE",
    "APOLOGIZE",
    "LISTEN",
    "CELEBRATE",
    "NORMALIZE",
    "REDIRECT",
)

FRUSTRATION_HIGH = 0.6
DISENGAGEMENT_HIGH = 0.6
SUCCESS_HIGH = 0.6

# Deterministic guardrails (plan §51 item 30): below this interruptibility the
# user is not available for speech, so empathy strategies yield to GIVE_SPACE.
INTERRUPTIBILITY_FLOOR = 0.1


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class EmpathyEvidence:
    """Observable signals the policy may use (all optional)."""

    frustration: float = 0.0
    novi_caused_problem: bool = False
    disengagement: float = 0.0
    success: float = 0.0
    user_asked_for_space: bool = False
    interruptibility: float = 1.0
    boundary_state: str = ""
    context: dict[str, Any] = field(default_factory=dict)


class EmpathyPolicy:
    """Selects behavioral empathy strategies from evidence (plan §14)."""

    def select(self, evidence: EmpathyEvidence) -> list[str]:
        # Deterministic guardrails always win (plan §51 item 30): when the
        # user is not interruptible or has set a DO_NOT_INTERRUPT boundary,
        # the mature emotional response is to give space, not to speak.
        if _clamp01(evidence.interruptibility) < INTERRUPTIBILITY_FLOOR:
            return ["GIVE_SPACE"]
        if evidence.boundary_state == "DO_NOT_INTERRUPT":
            return ["GIVE_SPACE"]

        frustration = _clamp01(evidence.frustration)
        disengagement = _clamp01(evidence.disengagement)
        success = _clamp01(evidence.success)

        strategies: list[str] = []

        if frustration >= FRUSTRATION_HIGH:
            strategies.append("ACKNOWLEDGE")
            if evidence.novi_caused_problem:
                strategies.append("APOLOGIZE")
            strategies.append("SOLVE")
        elif frustration > 0.0:
            strategies.append("ACKNOWLEDGE")

        if disengagement >= DISENGAGEMENT_HIGH or evidence.user_asked_for_space:
            strategies.append("GIVE_SPACE")

        if success >= SUCCESS_HIGH:
            strategies.append("CELEBRATE")

        if not strategies:
            strategies.append("LISTEN")
        return strategies
