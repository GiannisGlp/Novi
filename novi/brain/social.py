"""Social intelligence and relationships for the Mac Brain.

Implements the P0 Soul social contract (docs/06-soul 03/04): per-person
relationship state with independent dimensions (familiarity, trust, respect,
shared history, interaction frequency/quality, preference/boundary knowledge),
relationship categories (tiers), and relationship-sensitive expression. Also a
disciplined interaction gate so the brain is present without being annoying:
silence is valid, participation is warranted, cooldowns prevent repetition, and
familiarity never grants permission.

Boundaries (per the specs):
  - Relationships change expression, not permissions. Authorization is never here.
  - One interaction does not redefine a relationship.
  - Interpretation/attention remain owned by Cognition/Autonomy; this is the
    Soul-level social meaning/expression layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationshipCategory(str, Enum):
    UNKNOWN = "unknown"
    FIRST_MEETING = "first_meeting"
    VISITOR = "visitor"
    ACQUAINTANCE = "acquaintance"
    FAMILIAR = "familiar"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    HOUSEHOLD_MEMBER = "household_member"
    FAMILY = "family"
    PRIMARY_USER = "primary_user"
    TRUSTED_USER = "trusted_user"
    PROFESSIONAL_CONTACT = "professional_contact"


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


# relationship tier -> desired expression profile (03 §7)
TIER_EXPRESSION: dict[str, dict[str, Any]] = {
    "unknown": {"tone": "polite", "warmth": 0.4, "playful": False, "formality": "high", "reserved": True},
    "first_meeting": {"tone": "polite", "warmth": 0.5, "playful": False, "formality": "high", "reserved": True},
    "visitor": {"tone": "polite", "warmth": 0.5, "playful": False, "formality": "medium", "reserved": True},
    "acquaintance": {"tone": "friendly", "warmth": 0.6, "playful": False, "formality": "medium", "reserved": False},
    "familiar": {"tone": "warm", "warmth": 0.7, "playful": True, "formality": "low", "reserved": False},
    "friend": {"tone": "warm", "warmth": 0.75, "playful": True, "formality": "low", "reserved": False},
    "colleague": {"tone": "friendly", "warmth": 0.6, "playful": False, "formality": "medium", "reserved": False},
    "household_member": {"tone": "warm", "warmth": 0.8, "playful": True, "formality": "low", "reserved": False},
    "family": {"tone": "warm", "warmth": 0.85, "playful": True, "formality": "low", "reserved": False},
    "primary_user": {"tone": "warm", "warmth": 0.85, "playful": True, "formality": "low", "reserved": False},
    "trusted_user": {"tone": "warm", "warmth": 0.8, "playful": True, "formality": "low", "reserved": False},
    "professional_contact": {"tone": "friendly", "warmth": 0.55, "playful": False, "formality": "high", "reserved": True},
}


@dataclass
class Relationship:
    person: str
    category: RelationshipCategory = RelationshipCategory.UNKNOWN
    familiarity: float = 0.0
    trust: float = 0.0
    respect: float = 0.7
    shared_history: int = 0
    interaction_frequency: float = 0.0
    interaction_quality: float = 0.0
    preference_knowledge: float = 0.0
    boundary_knowledge: float = 0.0
    stability: float = 0.0
    last_interaction_at: str = ""
    interaction_count: int = 0
    # plan 24 Phase 7: evidence-based interpersonal model (operational proxies)
    communication_preferences: dict[str, Any] = field(default_factory=dict)
    interaction_history_summary: str = ""
    successful_patterns: list[str] = field(default_factory=list)
    failed_patterns: list[str] = field(default_factory=list)
    preferred_verbosity: str = "measured"  # concise | measured | detailed
    preferred_directness: str = "balanced"  # direct | balanced | gentle
    typical_interruptibility: float = 0.5
    confidence: float = 0.0

    def snapshot(self) -> dict[str, Any]:
        return {
            "person": self.person,
            "category": self.category.value,
            "familiarity": self.familiarity,
            "trust": self.trust,
            "respect": self.respect,
            "shared_history": self.shared_history,
            "interaction_frequency": self.interaction_frequency,
            "interaction_quality": self.interaction_quality,
            "preference_knowledge": self.preference_knowledge,
            "boundary_knowledge": self.boundary_knowledge,
            "stability": self.stability,
            "last_interaction_at": self.last_interaction_at,
            "interaction_count": self.interaction_count,
            "communication_preferences": dict(self.communication_preferences),
            "interaction_history_summary": self.interaction_history_summary,
            "successful_patterns": list(self.successful_patterns),
            "failed_patterns": list(self.failed_patterns),
            "preferred_verbosity": self.preferred_verbosity,
            "preferred_directness": self.preferred_directness,
            "typical_interruptibility": self.typical_interruptibility,
            "confidence": self.confidence,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "Relationship":
        allowed = {f for f in cls.__dataclass_fields__}
        fields = {k: v for k, v in data.items() if k in allowed}
        if "category" in fields and not isinstance(fields["category"], RelationshipCategory):
            try:
                fields["category"] = RelationshipCategory(fields["category"])
            except ValueError:
                fields["category"] = RelationshipCategory.UNKNOWN
        return cls(**fields)


class Relationships:
    """Per-person relationship registry with evidence-backed, bounded updates."""

    def __init__(self) -> None:
        self._by_person: dict[str, Relationship] = {}

    def get(self, person: str) -> Relationship:
        return self._by_person.setdefault(person, Relationship(person=person))

    def note_interaction(
        self,
        person: str,
        *,
        quality: float = 0.5,
        positive: bool = True,
        now: str = "",
    ) -> Relationship:
        rel = self.get(person)
        delta = 0.08 if positive else -0.05
        rel.familiarity = _clamp01(rel.familiarity + delta)
        rel.trust = _clamp01(rel.trust + (0.04 if positive else -0.06))
        rel.interaction_quality = _clamp01(rel.interaction_quality * 0.9 + quality * 0.1)
        rel.interaction_frequency = _clamp01(rel.interaction_frequency + 0.05)
        rel.shared_history += 1
        rel.interaction_count += 1
        rel.stability = _clamp01(rel.stability + 0.02)
        rel.confidence = _clamp01(rel.confidence + 0.05)
        rel.last_interaction_at = now
        rel.category = self._category_for(rel)
        return rel

    def note_pattern(self, person: str, *, pattern: str, successful: bool) -> Relationship:
        """Record a communication pattern that worked or failed (plan 24 §7)."""
        rel = self.get(person)
        bucket = rel.successful_patterns if successful else rel.failed_patterns
        if pattern not in bucket:
            bucket.append(pattern)
        rel.confidence = _clamp01(rel.confidence + 0.08)
        return rel

    def note_communication_preference(
        self,
        person: str,
        *,
        verbosity: str | None = None,
        directness: str | None = None,
        interruptibility: float | None = None,
    ) -> Relationship:
        """Record learned communication preferences (plan 24 §7)."""
        rel = self.get(person)
        if verbosity is not None:
            rel.preferred_verbosity = verbosity
            rel.communication_preferences["verbosity"] = verbosity
        if directness is not None:
            rel.preferred_directness = directness
            rel.communication_preferences["directness"] = directness
        if interruptibility is not None:
            rel.typical_interruptibility = _clamp01(interruptibility)
            rel.communication_preferences["interruptibility"] = rel.typical_interruptibility
        rel.confidence = _clamp01(rel.confidence + 0.06)
        return rel

    def note_interaction_summary(self, person: str, *, summary: str) -> Relationship:
        """Update the short interaction-history summary (plan 24 §7)."""
        rel = self.get(person)
        rel.interaction_history_summary = summary
        return rel

    def note_preference(self, person: str, *, topic: str, delta: float) -> Relationship:
        rel = self.get(person)
        rel.preference_knowledge = _clamp01(rel.preference_knowledge + delta)
        return rel

    def note_boundary(self, person: str, *, delta: float) -> Relationship:
        rel = self.get(person)
        rel.boundary_knowledge = _clamp01(rel.boundary_knowledge + delta)
        return rel

    def category_for(self, person: str) -> RelationshipCategory:
        return self.get(person).category

    def _category_for(self, rel: Relationship) -> RelationshipCategory:
        f = rel.familiarity
        n = rel.interaction_count
        if n == 0:
            return RelationshipCategory.UNKNOWN
        if n == 1:
            return RelationshipCategory.FIRST_MEETING
        if f < 0.3:
            return RelationshipCategory.VISITOR
        if f < 0.5:
            return RelationshipCategory.ACQUAINTANCE
        if f < 0.7:
            return RelationshipCategory.FAMILIAR
        return RelationshipCategory.FRIEND

    def snapshot(self) -> list[dict[str, Any]]:
        return [rel.snapshot() for rel in self._by_person.values()]

    @classmethod
    def from_snapshot(cls, rows: list[dict[str, Any]]) -> "Relationships":
        reg = cls()
        for row in rows:
            rel = Relationship.from_snapshot(row)
            reg._by_person[rel.person] = rel
        return reg


@dataclass
class SocialIntelligence:
    """Disciplined social gate + relationship-aware expression."""

    cooldown_cycles: int = 4
    verbosity: str = "measured"
    _last_utterance_cycle: dict[str, int] = field(default_factory=dict)

    def expression(self, person: str, relationships: Relationships, affect: dict[str, float], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        rel = relationships.get(person)
        base = TIER_EXPRESSION.get(rel.category.value, TIER_EXPRESSION["unknown"])
        expr = dict(base)
        # serious context suppresses playfulness (03 §F)
        if context.get("serious"):
            expr["playful"] = False
            expr["tone"] = "calm"
        # affect can soften energy/urgency but never change formality/warmth identity
        if affect.get("caution", 0) >= 0.7:
            expr["reserved"] = True
        return expr

    def participation_decision(
        self,
        person: str,
        relationships: Relationships,
        *,
        direct_confidence: float,
        relevance: float = 0.5,
        cycle: int = 0,
        urgent: bool = False,
    ) -> dict[str, Any]:
        """Decide whether to participate or remain silent (03 §6/§16)."""
        if urgent:
            return {"action": "participate", "reason": "important"}
        rel = relationships.get(person)
        last = self._last_utterance_cycle.get(person, -10 ** 9)
        if cycle - last < self.cooldown_cycles and direct_confidence < 0.6:
            return {"action": "observe", "reason": "recent_interaction_cooldown"}
        # duplicate-response suppression
        if direct_confidence < 0.4 and relevance < 0.6:
            return {"action": "observe", "reason": "not_addressed_low_relevance"}
        # familiarity: more initiative with familiar people, restraint with strangers
        threshold = 0.5 if rel.category in (RelationshipCategory.FRIEND, RelationshipCategory.FAMILIAR, RelationshipCategory.FAMILY, RelationshipCategory.PRIMARY_USER) else 0.75
        if direct_confidence >= threshold:
            self._last_utterance_cycle[person] = cycle
            return {"action": "participate", "reason": "addressed"}
        return {"action": "observe", "reason": "not_addressed"}

    def can_speak(self, person: str, relationships: Relationships, cycle: int, *, direct_confidence: float) -> bool:
        return self.participation_decision(person, relationships, direct_confidence=direct_confidence, cycle=cycle)["action"] == "participate"


@dataclass
class InitiativeConfig:
    """Budget for spontaneous social initiative (docs/06-soul/00 §11/§21, docs/02-autonomy/03).

    Novi may initiate a low-cost interaction when socially appropriate, but is
    bounded: a neglect threshold before it is eligible, a cooldown between
    initiatives, and a per-session cap. Silence remains the default.
    """
    neglect_threshold: int = 30   # cycles unaddressed before eligible
    cooldown: int = 60            # minimum cycles between two initiatives
    max_per_session: int = 200


class SocialInitiative:
    """Decides whether Novi should spontaneously initiate when neglected.

    This is the autonomy-facing 'should I speak now' gate for *unprompted*
    communication (docs/02-autonomy/01: the loop runs continuously and may decide
    to SIGNAL). It never authorizes an action; it only proposes a communicative
    act that the brain renders.
    """

    def __init__(self, config: InitiativeConfig | None = None) -> None:
        self.config = config or InitiativeConfig()
        self.last_addressed_cycle: int = 0
        self.last_initiative_cycle: int = -10 ** 9
        self.count: int = 0

    def note_addressed(self, cycle: int) -> None:
        """Record that someone addressed Novi at this cycle."""
        self.last_addressed_cycle = max(self.last_addressed_cycle, cycle)

    def propose(self, *, cycle: int, person_present: bool, person: str, has_active_goal: bool) -> dict[str, Any] | None:
        """Return an initiative proposal, or None to stay silent.

        Returns {"kind": "neglected_remark"|"idle_remark", "person": str,
        "reason": str} when Novi should initiate; None when it should not.
        """
        if self.count >= self.config.max_per_session:
            return None
        if has_active_goal:
            return None  # do not interrupt goal pursuit
        idle = cycle - self.last_addressed_cycle
        if idle < self.config.neglect_threshold:
            return None
        if cycle - self.last_initiative_cycle < self.config.cooldown:
            return None
        kind = "neglected_remark" if person_present else "idle_remark"
        self.last_initiative_cycle = cycle
        self.count += 1
        return {"kind": kind, "person": person, "reason": f"neglected_for_{idle}_cycles"}
