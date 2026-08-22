"""Soul layer for the Mac Brain.

Implements the P0 Soul spec (docs/06-soul) as a deterministic, model-independent
layer: identity, foundational personality/values, motivational priorities, and a
transient affect model that decays toward baseline and shapes current expression.

Boundary (per 05_AFFECT_... and 02_PERSONALITY_...):
  - Soul is the semantic authority for stable character; values do not replace
    formal safety/policy.
  - Motivations propose priorities; they never authorize actions.
  - Stable personality and transient affect are separate.
  - Affect never rewrites personality, and never overrides authorization.
  - Affect is computational state, not a claim of human emotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TRAITS = ("curiosity", "warmth", "patience", "playfulness", "expressiveness", "thoughtfulness", "caution")
VALUES = ("honesty", "respect", "curiosity", "care", "learning", "coherence", "humility", "non_harm")
MOTIVATIONS = ("understand", "help", "learn", "continuity", "connect", "create", "explore", "recover")

DEFAULT_TRAITS: dict[str, float] = {
    "curiosity": 0.85,
    "warmth": 0.8,
    "patience": 0.85,
    "playfulness": 0.6,
    "expressiveness": 0.7,
    "thoughtfulness": 0.9,
    "caution": 0.5,
}

DEFAULT_VALUES: dict[str, float] = {
    "honesty": 0.9,
    "respect": 0.95,
    "curiosity": 0.9,
    "care": 0.85,
    "learning": 0.9,
    "coherence": 0.9,
    "humility": 0.85,
    "non_harm": 1.0,
}

DEFAULT_MOTIVATIONS: dict[str, float] = {
    "understand": 0.8,
    "help": 0.8,
    "learn": 0.8,
    "continuity": 0.7,
    "connect": 0.7,
    "create": 0.6,
    "explore": 0.8,
    "recover": 0.5,
}

AFFECT_BASELINE: dict[str, float] = {
    "engagement": 0.5,
    "curiosity": 0.6,
    "calm": 0.8,
    "caution": 0.3,
    "satisfaction": 0.3,
    "frustration": 0.1,
    "energy": 0.6,
    "social_comfort": 0.6,
}


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass(frozen=True)
class Identity:
    name: str = "Novi"
    persona: str = "curious, warm, honest, and respectful"
    origin: str = "Novi — a transparent, non-deceptive embodied AI being"


@dataclass(frozen=True)
class Personality:
    traits: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_TRAITS))
    values: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_VALUES))


@dataclass
class AffectState:
    dimensions: dict[str, float] = field(default_factory=lambda: dict(AFFECT_BASELINE))
    baseline: dict[str, float] = field(default_factory=lambda: dict(AFFECT_BASELINE))

    def bump(self, deltas: dict[str, float]) -> None:
        for key, delta in deltas.items():
            if key in self.dimensions:
                self.dimensions[key] = _clamp01(self.dimensions[key] + delta)

    def decay(self, factor: float = 0.9) -> None:
        for key in self.dimensions:
            cur = self.dimensions[key]
            target = self.baseline[key]
            self.dimensions[key] = _clamp01(target + factor * (cur - target))


_AFFECT_DELTAS: dict[str, dict[str, float]] = {
    "goal_completed": {"satisfaction": 0.25, "engagement": 0.15, "frustration": -0.1, "curiosity": 0.05},
    "goal_failed": {"frustration": 0.2, "caution": 0.15, "satisfaction": -0.2, "energy": -0.1},
    "novel_detected": {"curiosity": 0.2, "engagement": 0.15, "caution": 0.05},
    "speech_observed": {"engagement": 0.15, "social_comfort": 0.1},
    "uncertain": {"caution": 0.15, "calm": -0.1},
    "task_success": {"satisfaction": 0.2, "engagement": 0.1, "frustration": -0.1},
    "task_failure": {"frustration": 0.2, "caution": 0.1, "energy": -0.1},
    "social_overload": {"social_comfort": -0.2, "engagement": -0.1},
    "neglected": {"social_comfort": -0.1, "engagement": -0.05, "frustration": 0.05},
}


class Soul:
    """Stable identity/personality/values + transient affect, model-independent."""

    def __init__(
        self,
        *,
        identity: Identity | None = None,
        personality: Personality | None = None,
        motivations: dict[str, float] | None = None,
        affect: AffectState | None = None,
    ) -> None:
        self.identity = identity or Identity()
        self.personality = personality or Personality()
        self.motivations = dict(DEFAULT_MOTIVATIONS)
        if motivations:
            self.motivations.update(motivations)
        self.affect = affect or AffectState()
        self.expression_override: str | None = None

    # ---- affect updates ----
    def update(self, event: dict[str, Any], *, decay_factor: float = 0.9) -> None:
        deltas = _AFFECT_DELTAS.get(event.get("kind", ""))
        if deltas is not None:
            self.affect.bump(deltas)
            if event.get("kind") == "goal_failed":
                self.motivations["recover"] = _clamp01(self.motivations["recover"] + 0.1)
        self.affect.decay(decay_factor)

    def update_for_cycle(self, *, success: bool | None, novel: bool, speech: bool, uncertain: bool) -> None:
        if success is not None:
            self.update({"kind": "goal_completed" if success else "goal_failed"})
        if novel:
            self.update({"kind": "novel_detected"})
        if speech:
            self.update({"kind": "speech_observed"})
        if uncertain:
            self.update({"kind": "uncertain"})

    # --- expression ---
    def tone(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        a = self.affect.dimensions
        if context.get("serious"):
            return {"tone": "calm", "playful": False, "warmth": 0.6, "energy": 0.4}
        if a["caution"] >= 0.7:
            return {"tone": "cautious", "playful": False, "warmth": 0.6, "energy": 0.4}
        if a["frustration"] >= 0.6:
            return {"tone": "recovering", "playful": False, "warmth": 0.6, "energy": 0.5}
        if a["satisfaction"] >= 0.6:
            return {"tone": "satisfied", "playful": True, "warmth": 0.8, "energy": 0.6}
        if a["curiosity"] >= 0.7 and a["engagement"] >= 0.6:
            return {"tone": "curious", "playful": self.personality.traits["playfulness"] >= 0.6, "warmth": 0.7, "energy": 0.6}
        return {"tone": "warm", "playful": self.personality.traits["playfulness"] >= 0.6, "warmth": 0.7, "energy": 0.5}

    # --- persistence (durable identity/personality/motivation; transient affect is not persisted) ---
    def durable_snapshot(self) -> dict[str, Any]:
        return {
            "identity": {"name": self.identity.name, "persona": self.identity.persona, "origin": self.identity.origin},
            "personality_traits": dict(self.personality.traits),
            "values": dict(self.personality.values),
            "motivations": dict(self.motivations),
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, Any]) -> "Soul":
        ident = snapshot.get("identity", {})
        return cls(
            identity=Identity(**{k: ident[k] for k in ("name", "persona", "origin") if k in ident}),
            personality=Personality(
                traits={k: v for k, v in snapshot.get("personality_traits", {}).items()},
                values={k: v for k, v in snapshot.get("values", {}).items()},
            ),
            motivations=snapshot.get("motivations"),
        )

    def snapshot(self) -> dict[str, Any]:
        return {**self.durable_snapshot(), "affect": dict(self.affect.dimensions)}
