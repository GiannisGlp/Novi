"""Context Assembler for the Mac Brain (PERFECTING_PLAN Step 1).

Constructs the smallest sufficient context for cognition, reasoning, and
dialogue from the current world state, relevant memory, knowledge, social
context, active goals, and recent events.

Canonical authority: docs/03-cognition/09_CONTEXT_ENGINE.md

Key design principles:
  - Context is bounded (token/context budget), not maximum-retrieval volume.
  - Every retrieved item retains its source and confidence (provenance preserved).
  - Conflicting memories or knowledge are represented explicitly, not collapsed.
  - Privacy filtering: only the minimum world state required for the task.
  - Model independence: produces a structured semantic package, not a prompt.

The "Bring me that cup" reference-resolution case:
  Given a speaker utterance + current world state, the ContextAssembler
  assembles the context needed to resolve "that cup" to a specific entity:
  current speaker, location, visible objects, recent events, current goal,
  spatial relations, uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .world_model import (
    INFERRED,
    OBSERVED,
    UNKNOWN,
    VERIFIED,
    WorldModel,
)

# ---------------------------------------------------------------------------
# ContextPackage — the output of the ContextAssembler
# ---------------------------------------------------------------------------

@dataclass
class ContextItem:
    """A single item in the context package with provenance."""
    layer: str  # immediate | situational | memory | knowledge | relationship | long-horizon
    kind: str  # entity | relation | event | goal | memory | speaker | uncertainty
    data: dict[str, Any]
    source: str = ""
    confidence: float = 0.0
    epistemic_status: str = UNKNOWN

    def snapshot(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "kind": self.kind,
            "data": self.data,
            "source": self.source,
            "confidence": round(self.confidence, 4),
            "epistemic_status": self.epistemic_status,
        }


@dataclass
class ContextPackage:
    """A bounded, provenance-filtered context package for reasoning/dialogue."""
    items: list[ContextItem] = field(default_factory=list)
    token_budget: int = 0
    items_dropped: int = 0
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    privacy_filtered: bool = False

    def by_layer(self, layer: str) -> list[ContextItem]:
        return [item for item in self.items if item.layer == layer]

    def entities(self) -> list[ContextItem]:
        return [item for item in self.items if item.kind == "entity"]

    def relations(self) -> list[ContextItem]:
        return [item for item in self.items if item.kind == "relation"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.snapshot() for item in self.items],
            "token_budget": self.token_budget,
            "items_dropped": self.items_dropped,
            "contradictions": list(self.contradictions),
            "privacy_filtered": self.privacy_filtered,
            "item_count": len(self.items),
        }


# ---------------------------------------------------------------------------
# ContextAssembler
# ---------------------------------------------------------------------------

# Rough token estimate: 1 token ≈ 4 characters of JSON text.
_CHARS_PER_TOKEN = 4

# Layers (docs/03-cognition/09 §Context Layers)
LAYER_IMMEDIATE = "immediate"
LAYER_SITUATIONAL = "situational"
LAYER_MEMORY = "memory"
LAYER_KNOWLEDGE = "knowledge"
LAYER_RELATIONSHIP = "relationship"
LAYER_LONG_HORIZON = "long-horizon"


@dataclass
class ContextRequest:
    """A request for context assembly."""
    task_type: str = "dialogue"  # dialogue | reasoning | planning | reference_resolution
    speaker_id: str | None = None
    speaker_label: str | None = None
    location: str | None = None
    utterance: str | None = None
    goal: dict[str, Any] | None = None
    recent_events: tuple[dict[str, Any], ...] = ()
    recalled_memories: tuple[dict[str, Any], ...] = ()
    knowledge_triples: tuple[dict[str, Any], ...] = ()
    token_budget: int = 2000
    privacy_scope: str = "default"  # default | restricted | internal
    referenced_labels: tuple[str, ...] = ()  # labels mentioned in utterance for reference resolution
    situations: tuple[dict[str, Any], ...] = ()  # derived situations from SituationModel


class ContextAssembler:
    """Assembles a bounded, provenance-filtered context package.

    Usage:
        ctx = assembler.assemble(world_model, request)
        package = ctx  # ContextPackage

    The assembler:
      1. Pulls immediate layer (current speaker, location, visible objects).
      2. Pulls situational layer (active people, recent events, spatial relations).
      3. Pulls relevant memory (recalled_memories passed in).
      4. Pulls knowledge (knowledge_triples passed in).
      5. Pulls relationship layer (speaker's relationship info if available).
      6. Pulls long-horizon (active goal).
      7. Ranks by relevance/freshness/confidence and trims to token budget.
      8. Preserves contradictions explicitly.
      9. Privacy-filters based on the request's privacy_scope.
    """

    def assemble(self, world: WorldModel, request: ContextRequest) -> ContextPackage:
        items: list[ContextItem] = []
        contradictions: list[dict[str, Any]] = []

        # ---- Layer 1: Immediate ----
        items.extend(self._immediate_layer(world, request))

        # ---- Layer 2: Situational ----
        items.extend(self._situational_layer(world, request))

        # ---- Layer 3: Relevant memory ----
        items.extend(self._memory_layer(request))

        # ---- Layer 4: Knowledge ----
        items.extend(self._knowledge_layer(request))

        # ---- Layer 5: Relationship ----
        items.extend(self._relationship_layer(world, request))

        # ---- Layer 5b: Situations (from SituationModel) ----
        items.extend(self._situations_layer(request))

        # ---- Layer 6: Long-horizon ----
        items.extend(self._long_horizon_layer(request))

        # ---- Contradictions ----
        for c in world.contradictions:
            if c.resolution == "unresolved":
                contradictions.append(c.snapshot())

        # ---- Rank and trim to budget ----
        ranked = self._rank(items, request)
        trimmed, dropped = self._trim_to_budget(ranked, request.token_budget)

        # ---- Privacy filter ----
        filtered = self._privacy_filter(trimmed, request.privacy_scope)

        return ContextPackage(
            items=filtered,
            token_budget=request.token_budget,
            items_dropped=dropped + (len(trimmed) - len(filtered)),
            contradictions=contradictions,
            privacy_filtered=request.privacy_scope != "internal",
        )

    # ---- layer builders ----

    def _immediate_layer(self, world: WorldModel, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []
        # Current speaker
        if request.speaker_id or request.speaker_label:
            speaker = world.resolve(request.speaker_label or request.speaker_id or "")
            if speaker is not None:
                items.append(ContextItem(
                    layer=LAYER_IMMEDIATE, kind="speaker",
                    data={"entity_id": speaker.entity_id, "label": speaker.label(), "type": speaker.entity_type},
                    source=speaker.provenance.source if speaker.provenance else "",
                    confidence=speaker.confidence,
                    epistemic_status=speaker.epistemic_status,
                ))
            elif request.speaker_label:
                items.append(ContextItem(
                    layer=LAYER_IMMEDIATE, kind="speaker",
                    data={"label": request.speaker_label, "type": "person", "entity_id": None},
                    source="utterance", confidence=0.5, epistemic_status=UNKNOWN,
                ))
        # Current location
        if request.location:
            items.append(ContextItem(
                layer=LAYER_IMMEDIATE, kind="entity",
                data={"field": "location", "value": request.location},
                source="request", confidence=1.0, epistemic_status=OBSERVED,
            ))
        # Current utterance
        if request.utterance:
            items.append(ContextItem(
                layer=LAYER_IMMEDIATE, kind="event",
                data={"type": "utterance", "text": request.utterance, "speaker": request.speaker_label},
                source="stt", confidence=1.0, epistemic_status=OBSERVED,
            ))
        # Visible objects at current location
        visible = world.visible_entities(location=request.location)
        for entity in visible:
            if entity.entity_type in ("object", "device"):
                items.append(ContextItem(
                    layer=LAYER_IMMEDIATE, kind="entity",
                    data=entity.snapshot(),
                    source=entity.provenance.source if entity.provenance else "",
                    confidence=entity.confidence,
                    epistemic_status=entity.epistemic_status,
                ))
        return items

    def _situational_layer(self, world: WorldModel, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []
        # Active people
        for entity in world.visible_entities(location=request.location):
            if entity.entity_type == "person":
                items.append(ContextItem(
                    layer=LAYER_SITUATIONAL, kind="entity",
                    data=entity.snapshot(),
                    source=entity.provenance.source if entity.provenance else "",
                    confidence=entity.confidence,
                    epistemic_status=entity.epistemic_status,
                ))
        # Recent events
        for event in request.recent_events[-10:]:  # bounded
            items.append(ContextItem(
                layer=LAYER_SITUATIONAL, kind="event",
                data=event, source=event.get("source", ""), confidence=event.get("confidence", 0.5),
                epistemic_status=event.get("epistemic_status", OBSERVED),
            ))
        # Spatial relations at current location
        if request.location:
            for entity in world.visible_entities(location=request.location):
                for rel in world.relations_for(entity.entity_id):
                    if rel.is_active():
                        items.append(ContextItem(
                            layer=LAYER_SITUATIONAL, kind="relation",
                            data=rel.snapshot(),
                            source=rel.provenance.source if rel.provenance else "",
                            confidence=rel.confidence,
                            epistemic_status=rel.epistemic_status,
                        ))
        return items

    def _memory_layer(self, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []
        for mem in request.recalled_memories:
            items.append(ContextItem(
                layer=LAYER_MEMORY, kind="memory",
                data=mem, source=mem.get("source", "memory"), confidence=mem.get("confidence", 0.5),
                epistemic_status=mem.get("epistemic_status", INFERRED),
            ))
        return items

    def _knowledge_layer(self, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []
        for triple in request.knowledge_triples:
            items.append(ContextItem(
                layer=LAYER_KNOWLEDGE, kind="relation",
                data=triple, source=triple.get("source", "knowledge"), confidence=triple.get("confidence", 0.5),
                epistemic_status=triple.get("epistemic_status", VERIFIED),
            ))
        return items

    def _relationship_layer(self, world: WorldModel, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []
        if request.speaker_id:
            for rel in world.relations_for(request.speaker_id):
                if rel.relation_type in ("knows", "friends_with", "family_of", "colleague_of"):
                    items.append(ContextItem(
                        layer=LAYER_RELATIONSHIP, kind="relation",
                        data=rel.snapshot(),
                        source=rel.provenance.source if rel.provenance else "",
                        confidence=rel.confidence,
                        epistemic_status=rel.epistemic_status,
                    ))
        return items

    def _situations_layer(self, request: ContextRequest) -> list[ContextItem]:
        """Include derived situations from the SituationModel in the context."""
        items: list[ContextItem] = []
        for sit in request.situations:
            items.append(ContextItem(
                layer=LAYER_SITUATIONAL, kind="situation",
                data=sit,
                source=sit.get("provenance", {}).get("source", "situation_model"),
                confidence=sit.get("confidence", 0.5),
                epistemic_status=sit.get("freshness", "fresh").upper() if isinstance(sit.get("freshness"), str) else "FRESH",
            ))
        return items

    def _long_horizon_layer(self, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []
        if request.goal:
            items.append(ContextItem(
                layer=LAYER_LONG_HORIZON, kind="goal",
                data=request.goal, source="autonomy", confidence=1.0, epistemic_status=OBSERVED,
            ))
        return items

    # ---- ranking and trimming ----

    def _rank(self, items: list[ContextItem], request: ContextRequest) -> list[ContextItem]:
        """Rank by layer priority, relevance to referenced labels, confidence, and freshness."""
        layer_priority = {
            LAYER_IMMEDIATE: 0,
            LAYER_SITUATIONAL: 1,
            LAYER_RELATIONSHIP: 2,
            LAYER_MEMORY: 3,
            LAYER_KNOWLEDGE: 4,
            LAYER_LONG_HORIZON: 5,
        }
        ref_set = {lbl.lower() for lbl in request.referenced_labels}

        def score(item: ContextItem) -> tuple[int, float, float]:
            # Lower layer_priority = higher rank (immediate first).
            lp = layer_priority.get(item.layer, 99)
            # Relevance boost if the item mentions a referenced label.
            relevance = 0.0
            if ref_set:
                data_str = str(item.data).lower()
                if any(ref in data_str for ref in ref_set):
                    relevance = 1.0
            # Confidence.
            conf = item.confidence
            # Ascending sort: negate relevance/confidence so higher values rank
            # first (relevant, high-confidence items are kept when trimming).
            return (lp, -relevance, -conf)

        return sorted(items, key=score)

    def _trim_to_budget(self, items: list[ContextItem], budget: int) -> tuple[list[ContextItem], int]:
        """Trim items to fit the token budget. Returns (kept, dropped_count)."""
        kept: list[ContextItem] = []
        total_chars = 0
        dropped = 0
        for item in items:
            item_chars = len(str(item.snapshot()))
            if total_chars + item_chars > budget * _CHARS_PER_TOKEN:
                dropped = len(items) - len(kept)
                break
            kept.append(item)
            total_chars += item_chars
        return kept, dropped

    def _privacy_filter(self, items: list[ContextItem], privacy_scope: str) -> list[ContextItem]:
        """Filter items based on privacy scope.

        - internal: no filtering (full access for internal reasoning).
        - default: drop items with privacy_class = "restricted" or "private".
        - restricted: drop items with privacy_class != "unclassified".
        """
        if privacy_scope == "internal":
            return items
        filtered: list[ContextItem] = []
        for item in items:
            privacy = item.data.get("privacy_class", "unclassified") if isinstance(item.data, dict) else "unclassified"
            if privacy_scope == "restricted" and privacy != "unclassified":
                continue
            if privacy_scope == "default" and privacy in ("restricted", "private"):
                continue
            filtered.append(item)
        return filtered

    # ---- reference resolution ----

    def resolve_reference(
        self,
        world: WorldModel,
        request: ContextRequest,
        referent_phrase: str,
    ) -> dict[str, Any]:
        """Resolve a referring expression (e.g. "that cup") to a world entity.

        This implements the NVIDIA Experiment 1 "Bring me that cup" case:
        given the current speaker, location, visible objects, spatial relations,
        and uncertainty, resolve the referent to a specific entity or return
        AMBIGUOUS/UNKNOWN.

        Returns:
            {"entity_id": str|None, "label": str|None, "status": "RESOLVED"|"AMBIGUOUS"|"UNKNOWN",
             "candidates": [...], "confidence": float, "context": ContextPackage}
        """
        ctx = self.assemble(world, request)

        # Extract the head noun from the referent phrase (e.g. "that cup" -> "cup").
        head = referent_phrase.lower().strip()
        for prefix in ("that ", "this ", "the ", "a ", "an ", "my "):
            if head.startswith(prefix):
                head = head[len(prefix):]
                break

        # Find candidates among all entities matching the head noun.
        # We search the full world model (not just the bounded context) so that
        # referents not currently visible but nearby can still be resolved.
        candidates: list[dict[str, Any]] = []
        for entity in world.entities.values():
            if entity.lifecycle in ("archived", "superseded"):
                continue
            all_names = [lbl.lower() for lbl in entity.labels] + [a.lower() for a in entity.aliases]
            if head in all_names or head in entity.entity_type or any(head in n for n in all_names):
                candidates.append({
                    "entity_id": entity.entity_id,
                    "label": entity.label(),
                    "entity_type": entity.entity_type,
                    "confidence": entity.confidence,
                    "epistemic_status": entity.epistemic_status,
                    "location": entity.state_value("location"),
                })

        if len(candidates) == 0:
            return {
                "entity_id": None, "label": None, "status": "UNKNOWN",
                "candidates": [], "confidence": 0.0, "context": ctx,
            }
        if len(candidates) == 1:
            best = candidates[0]
            return {
                "entity_id": best["entity_id"], "label": best["label"], "status": "RESOLVED",
                "candidates": candidates, "confidence": best["confidence"], "context": ctx,
            }
        # Multiple candidates: return AMBIGUOUS with all ranked by confidence.
        candidates.sort(key=lambda c: -c["confidence"])
        return {
            "entity_id": None, "label": None, "status": "AMBIGUOUS",
            "candidates": candidates, "confidence": candidates[0]["confidence"], "context": ctx,
        }
