"""Situation Model for the Mac Brain.

Interprets world state into meaningful current contexts. A situation is an
interpretation of current context, not a replacement for the World Model.
Situations can overlap and have confidence, evidence, freshness and expiration.

Canonical authority: docs/03-cognition/01_COGNITIVE_ARCHITECTURE.md §Situation Model

The Situation Model exposes:
  situation_id, world_state_version, active_entities, active_events,
  active_activities, relationships, Novi_state, current_place,
  active_goals/tasks, attention_targets, hazards/opportunities,
  social/interaction context, recent_changes, predictions,
  uncertainties, provenance, freshness.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import uuid4

from .world_model import PERSON, UNKNOWN, WorldModel

# ---------------------------------------------------------------------------
# Situation — one interpreted current context
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Situation:
    """A derived interpretation of the current world state.

    Situations can overlap (multiple can be active simultaneously) and have
    confidence, evidence, freshness, and expiration.
    """
    situation_id: str
    situation_type: str  # person_present | conversation_occurring | navigation_blocked | unfamiliar_object | idle | observing | goal_pursuit | etc.
    label: str  # human-readable description
    confidence: float
    world_state_version: int
    active_entities: tuple[str, ...]
    active_events: tuple[str, ...]
    active_activities: tuple[str, ...]
    relationships: tuple[str, ...]
    novi_state: dict[str, Any]
    current_place: str | None
    active_goals: tuple[str, ...]
    attention_targets: tuple[str, ...]
    hazards: tuple[str, ...]
    opportunities: tuple[str, ...]
    social_context: dict[str, Any]
    recent_changes: tuple[str, ...]
    predictions: tuple[str, ...]
    uncertainties: tuple[str, ...]
    provenance: dict[str, Any]
    freshness: str  # fresh | recent | stale
    created_at: str
    expires_at: str | None = None  # None = no expiration

    def snapshot(self) -> dict[str, Any]:
        return {
            "situation_id": self.situation_id,
            "situation_type": self.situation_type,
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "world_state_version": self.world_state_version,
            "active_entities": list(self.active_entities),
            "active_events": list(self.active_events),
            "active_activities": list(self.active_activities),
            "relationships": list(self.relationships),
            "novi_state": dict(self.novi_state),
            "current_place": self.current_place,
            "active_goals": list(self.active_goals),
            "attention_targets": list(self.attention_targets),
            "hazards": list(self.hazards),
            "opportunities": list(self.opportunities),
            "social_context": dict(self.social_context),
            "recent_changes": list(self.recent_changes),
            "predictions": list(self.predictions),
            "uncertainties": list(self.uncertainties),
            "provenance": dict(self.provenance),
            "freshness": self.freshness,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


# ---------------------------------------------------------------------------
# SituationModel — derives situations from the world model
# ---------------------------------------------------------------------------

class SituationModel:
    """Derives meaningful situations from the current world state.

    The SituationModel interprets the WorldModel's current state into
    overlapping situations with confidence, evidence, and freshness.
    It is consumed by the ContextAssembler and the reasoning engine.
    """

    def __init__(self) -> None:
        self._situations: list[Situation] = []
        self._last_world_version: int = -1

    def derive(
        self,
        world: WorldModel,
        *,
        novi_state: dict[str, Any] | None = None,
        active_goals: Sequence[str] = (),
        recent_events: Sequence[dict[str, Any]] = (),
        social_context: dict[str, Any] | None = None,
        cycle: int = 0,
    ) -> tuple[Situation, ...]:
        """Derive current situations from the world model.

        Returns a tuple of active Situation objects.
        """
        now = datetime.now(timezone.utc).isoformat()
        novi_state = novi_state or {}
        social_context = social_context or {}
        world_version = world.world_version
        prev_version = self._last_world_version
        self._last_world_version = world_version

        # Collect active entities.
        entities = world.visible_entities()
        active_entity_ids = tuple(e.entity_id for e in entities)
        active_entity_labels = tuple(e.label() for e in entities)

        # Collect relationships from the world model.
        all_relations: list[str] = []
        for entity in entities:
            for rel in world.relations_for(entity.entity_id):
                all_relations.append(f"{rel.subject_id} {rel.relation_type} {rel.object_id}")

        # Collect uncertainties.
        uncertainties: list[str] = []
        uncertainty_summary = world.uncertainty_summary()
        for uid in uncertainty_summary.get("uncertain_entities", []):
            uncertainties.append(f"entity:{uid}:epistemic_status_unknown")
        unresolved = uncertainty_summary.get("unresolved_contradictions", 0)
        if unresolved > 0:
            uncertainties.append(f"contradictions:{unresolved}:unresolved")

        # Collect hazards and opportunities.
        hazards: list[str] = []
        opportunities: list[str] = []
        for entity in entities:
            if entity.epistemic_status == UNKNOWN:
                opportunities.append(f"investigate:{entity.label()}")
            state_val = entity.state_value("state")
            if isinstance(state_val, str) and state_val in ("open", "alert", "emergency"):
                hazards.append(f"entity:{entity.label()}:state={state_val}")

        # Collect recent changes.
        recent_changes: list[str] = []
        for event in recent_events[-10:]:
            etype = event.get("event_type", event.get("type", "unknown"))
            recent_changes.append(str(etype))

        # Determine current place (from entities with location).
        current_place = None
        for entity in entities:
            loc = entity.state_value("location")
            if loc and entity.entity_type in ("room", "place", "building"):
                current_place = str(loc)
                break

        # Collect predictions (from entities with PREDICTED status).
        predictions: list[str] = []
        for entity in entities:
            if entity.epistemic_status == "PREDICTED":
                predictions.append(f"entity:{entity.label()}:predicted")

        # Determine freshness relative to the previously seen world version.
        # (prev_version is captured before _last_world_version is updated, so
        # this reflects actual change rather than always comparing to itself.)
        freshness = "fresh" if world_version > prev_version + 5 else "recent"
        if world_version == prev_version:
            freshness = "stale"

        situations: list[Situation] = []

        # ---- Situation: person_present ----
        person_entities = [e for e in entities if e.entity_type == PERSON]
        if person_entities:
            person_labels = [e.label() for e in person_entities]
            situations.append(Situation(
                situation_id=str(uuid4()),
                situation_type="person_present",
                label=f"Person(s) present: {', '.join(person_labels)}",
                confidence=max(e.confidence for e in person_entities),
                world_state_version=world_version,
                active_entities=tuple(e.entity_id for e in person_entities),
                active_events=(),
                active_activities=(),
                relationships=tuple(r for r in all_relations if any(p.entity_id in r for p in person_entities)),
                novi_state=novi_state,
                current_place=current_place,
                active_goals=tuple(active_goals),
                attention_targets=tuple(person_labels),
                hazards=hazards,
                opportunities=opportunities,
                social_context=social_context,
                recent_changes=tuple(recent_changes),
                predictions=tuple(predictions),
                uncertainties=tuple(uncertainties),
                provenance={"source": "situation_model", "cycle": cycle},
                freshness=freshness,
                created_at=now,
            ))

        # ---- Situation: conversation_occurring ----
        if social_context.get("conversation_active"):
            situations.append(Situation(
                situation_id=str(uuid4()),
                situation_type="conversation_occurring",
                label="Conversation is occurring",
                confidence=social_context.get("conversation_confidence", 0.8),
                world_state_version=world_version,
                active_entities=active_entity_ids,
                active_events=(),
                active_activities=("conversation",),
                relationships=tuple(all_relations),
                novi_state=novi_state,
                current_place=current_place,
                active_goals=tuple(active_goals),
                attention_targets=tuple(social_context.get("participants", [])),
                hazards=(),
                opportunities=(),
                social_context=social_context,
                recent_changes=tuple(recent_changes),
                predictions=(),
                uncertainties=(),
                provenance={"source": "situation_model", "cycle": cycle},
                freshness=freshness,
                created_at=now,
            ))

        # ---- Situation: unfamiliar_object_present ----
        unknown_entities = [e for e in entities if e.epistemic_status == UNKNOWN]
        if unknown_entities:
            unknown_labels = [e.label() for e in unknown_entities]
            situations.append(Situation(
                situation_id=str(uuid4()),
                situation_type="unfamiliar_object",
                label=f"Unfamiliar object(s) present: {', '.join(unknown_labels)}",
                confidence=0.5,  # uncertain
                world_state_version=world_version,
                active_entities=tuple(e.entity_id for e in unknown_entities),
                active_events=(),
                active_activities=(),
                relationships=(),
                novi_state=novi_state,
                current_place=current_place,
                active_goals=tuple(active_goals),
                attention_targets=tuple(unknown_labels),
                hazards=(),
                opportunities=[f"investigate:{lbl}" for lbl in unknown_labels],
                social_context=social_context,
                recent_changes=tuple(recent_changes),
                predictions=(),
                uncertainties=[f"entity:{lbl}:unknown" for lbl in unknown_labels],
                provenance={"source": "situation_model", "cycle": cycle},
                freshness=freshness,
                created_at=now,
            ))

        # ---- Situation: goal_pursuit ----
        if active_goals:
            situations.append(Situation(
                situation_id=str(uuid4()),
                situation_type="goal_pursuit",
                label=f"Pursuing goal(s): {', '.join(active_goals)}",
                confidence=0.9,
                world_state_version=world_version,
                active_entities=active_entity_ids,
                active_events=(),
                active_activities=("goal_pursuit",),
                relationships=tuple(all_relations),
                novi_state=novi_state,
                current_place=current_place,
                active_goals=tuple(active_goals),
                attention_targets=tuple(active_entity_labels),
                hazards=hazards,
                opportunities=opportunities,
                social_context=social_context,
                recent_changes=tuple(recent_changes),
                predictions=tuple(predictions),
                uncertainties=tuple(uncertainties),
                provenance={"source": "situation_model", "cycle": cycle},
                freshness=freshness,
                created_at=now,
            ))

        # ---- Situation: idle (default when nothing else is happening) ----
        if not situations:
            situations.append(Situation(
                situation_id=str(uuid4()),
                situation_type="idle",
                label="Idle — no significant activity",
                confidence=0.5,
                world_state_version=world_version,
                active_entities=active_entity_ids,
                active_events=(),
                active_activities=(),
                relationships=tuple(all_relations),
                novi_state=novi_state,
                current_place=current_place,
                active_goals=tuple(active_goals),
                attention_targets=(),
                hazards=(),
                opportunities=(),
                social_context=social_context,
                recent_changes=tuple(recent_changes),
                predictions=(),
                uncertainties=tuple(uncertainties),
                provenance={"source": "situation_model", "cycle": cycle},
                freshness=freshness,
                created_at=now,
            ))

        self._situations = situations
        return tuple(situations)

    @property
    def current_situations(self) -> tuple[Situation, ...]:
        return tuple(self._situations)

    def situations_of_type(self, situation_type: str) -> tuple[Situation, ...]:
        return tuple(s for s in self._situations if s.situation_type == situation_type)

    def snapshot(self) -> dict[str, Any]:
        return {
            "situations": [s.snapshot() for s in self._situations],
            "last_world_version": self._last_world_version,
            "situation_count": len(self._situations),
        }
