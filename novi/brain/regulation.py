"""Emotional regulation engine (plan 24, Phase 9).

Maps affective state + social context + relationship + conversation goal +
user availability + recent Novi behavior into behavior adjustments
(RegulationDecision). Regulation precedes generation (plan §2.6): emotional
signals change behavior appropriately without causing overreaction (Gate E3).

Deterministic and hardware-free: the engine is a pure function of its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

FRUSTRATION_HIGH = 0.6
FRUSTRATION_MODERATE = 0.35
TENSION_TENSE = "tense"


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class RegulationInput:
    """Observable inputs to the regulation engine (plan §13)."""

    affective_state: dict[str, Any] = field(default_factory=dict)
    social_context: dict[str, Any] = field(default_factory=dict)
    relationship: dict[str, Any] = field(default_factory=dict)
    conversation_goal: str = ""
    user_availability: str = "unknown"  # low | medium | high | unknown
    recent_novi_behavior: list[str] = field(default_factory=list)


@dataclass
class RegulationDecision:
    """Behavior adjustments produced by the regulation engine (plan §13)."""

    verbosity: str = "measured"  # concise | low | measured | high | detailed
    directness: str = "balanced"  # low | balanced | high
    empathy: str = "moderate"  # low | moderate | high
    humor: str = "moderate"  # low | moderate | high
    repetition_suppression: str = "none"  # none | mild | strong
    pace: str = "normal"  # slow | normal | fast
    question_frequency: str = "normal"  # low | normal | high
    acknowledgement_level: str = "normal"  # low | normal | high
    initiative_suppression: float = 0.0  # 0..1
    interruption_threshold: float = 0.5  # 0..1
    uncertainty_expression: str = "normal"  # low | normal | high
    repair_strategy: str = ""  # "" | apologize | clarify | rephrase | give_space

    def snapshot(self) -> dict[str, Any]:
        return {
            "verbosity": self.verbosity,
            "directness": self.directness,
            "empathy": self.empathy,
            "humor": self.humor,
            "repetition_suppression": self.repetition_suppression,
            "pace": self.pace,
            "question_frequency": self.question_frequency,
            "acknowledgement_level": self.acknowledgement_level,
            "initiative_suppression": round(self.initiative_suppression, 3),
            "interruption_threshold": round(self.interruption_threshold, 3),
            "uncertainty_expression": self.uncertainty_expression,
            "repair_strategy": self.repair_strategy,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "RegulationDecision":
        allowed = {f for f in cls.__dataclass_fields__}
        fields = {k: v for k, v in data.items() if k in allowed}
        return cls(**fields)


class RegulationEngine:
    """Deterministic regulation: affective signals → behavior adjustments."""

    def decide(self, inp: RegulationInput) -> RegulationDecision:
        d = RegulationDecision()
        frustration = _clamp01(float(inp.affective_state.get("frustration_likelihood", 0.0)))
        temperature = inp.social_context.get("conversation_temperature", "")
        repetitions = sum(1 for b in inp.recent_novi_behavior if "repeat" in b)

        # ---- verbosity: relationship preference is the baseline ----
        pref_verbosity = inp.relationship.get("preferred_verbosity", "")
        if pref_verbosity in ("concise", "low", "detailed", "high"):
            d.verbosity = pref_verbosity
        if frustration >= FRUSTRATION_HIGH:
            d.verbosity = "low"
        elif frustration >= FRUSTRATION_MODERATE and d.verbosity == "measured":
            d.verbosity = "concise"

        # ---- directness: high under frustration (plan §13 example) ----
        if frustration >= FRUSTRATION_HIGH:
            d.directness = "high"

        # ---- empathy: moderate under frustration, high when tense ----
        if frustration >= FRUSTRATION_HIGH:
            d.empathy = "moderate"
        if temperature == TENSION_TENSE:
            d.empathy = "high"

        # ---- humor: suppressed under frustration/tension ----
        if frustration >= FRUSTRATION_MODERATE or temperature == TENSION_TENSE:
            d.humor = "low"

        # ---- repetition suppression: strong when frustrated or repeating ----
        if frustration >= FRUSTRATION_HIGH or repetitions >= 2:
            d.repetition_suppression = "strong"
        elif repetitions == 1:
            d.repetition_suppression = "mild"

        # ---- pace: slower under frustration ----
        if frustration >= FRUSTRATION_HIGH:
            d.pace = "slow"

        # ---- question frequency: fewer questions when frustrated ----
        if frustration >= FRUSTRATION_MODERATE:
            d.question_frequency = "low"

        # ---- acknowledgement: higher when tense ----
        if temperature == TENSION_TENSE:
            d.acknowledgement_level = "high"

        # ---- initiative suppression + interruption threshold ----
        if inp.user_availability == "low":
            d.initiative_suppression = _clamp01(d.initiative_suppression + 0.6)
            d.interruption_threshold = _clamp01(d.interruption_threshold + 0.3)
        if frustration >= FRUSTRATION_HIGH:
            d.initiative_suppression = _clamp01(d.initiative_suppression + 0.4)
            d.interruption_threshold = _clamp01(d.interruption_threshold + 0.2)

        # ---- uncertainty expression: more honest when uncertain ----
        if frustration >= FRUSTRATION_HIGH:
            d.uncertainty_expression = "high"

        # ---- repair strategy: acknowledge and repair under tension ----
        if temperature == TENSION_TENSE or frustration >= FRUSTRATION_HIGH:
            if repetitions >= 2:
                d.repair_strategy = "rephrase"
            elif inp.conversation_goal == "solve_technical_problem":
                d.repair_strategy = "clarify"
            else:
                d.repair_strategy = "apologize"
        return d
