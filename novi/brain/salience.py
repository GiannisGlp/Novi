"""Event salience → autonomous utterance (plan 20, GAP-A/B/C).

Deterministic, brain-owned policy that turns non-text events (presence,
scene change, identity, hearing anomaly) into candidate proactive utterances,
gated by the same speaking-lease and initiative budget as neglect-driven
initiative. It never invents events — it only decides which already-drained
events are worth SAYING vs silently remembering (docs/plans/01_BRAIN/20 §3A).

The evaluator is pure and side-effect free: it takes drained event records plus
the set of entities Novi knows / currently sees, and returns at most one
CandidateInitiative per cycle (or None to stay silent). Naturalization of the
final spoken text happens in the engine's respond_event() so proactive remarks
read like Novi, not a canned string.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class CandidateInitiative:
    """A proactive communicative act proposed from a salient event.

    Mirrors the SocialInitiative.propose return shape, extended with the event
    provenance so the naturalizer can ground the remark.
    """

    kind: str
    entity: str
    text: str
    reason: str
    affordance: str
    source_event: dict


@dataclass
class EventSaliencePolicy:
    """Budget for event-driven autonomous speech (plan 20 §3A).

    Mirrors InitiativeConfig: a novelty threshold before an event is worth
    saying, a per-kind+entity cooldown to avoid repeating the same remark, and
    a per-window cap so proactive speech never floods the room.
    """

    novelty_threshold: float = 0.7
    cooldown_cycles: int = 60
    max_per_window: int = 3
    window_cycles: int = 300


# Event kind -> affordance (what the communicative act does).
_EVENT_AFFORDANCE: dict[str, str] = {
    "presence.entered": "greet",
    "presence.left": "note",
    "scene.changed": "comment",
    "identity.recognized": "greet",
    "identity.auto_enrolled": "ask",
    "hearing.anomaly": "ask",
    "person.holding": "comment",
    "object.novel": "ask",
    "object.recognized": "comment",
}


def _entity_of(event: dict, *, prefer: tuple[str, ...] = ()) -> str:
    """Extract a named entity from an event payload, if present.

    ``prefer`` keys are checked before the defaults so object-centric events
    (``person.holding``/``object.novel``) name the held object rather than the
    person holding it.
    """
    payload = event.get("payload")
    if isinstance(payload, dict):
        for key in (*prefer, "person", "entity", "name", "label", "object"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _novelty_of(event: dict) -> float:
    """Extract the novelty score from an event payload, defaulting to 0."""
    payload = event.get("payload")
    if isinstance(payload, dict):
        value = payload.get("novelty")
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


class SurgeSalienceEvaluator:
    """Deterministic gate: which drained events are worth a proactive remark.

    Stateful only in its cooldown/window bookkeeping (per-kind+entity last
    utterance cycle and a rolling per-window count). All salience decisions are
    pure functions of the event, the known/present entity sets, and that state.
    """

    def __init__(self, policy: EventSaliencePolicy | None = None) -> None:
        self.policy = policy or EventSaliencePolicy()
        self._last_utterance: dict[tuple[str, str], int] = {}
        self._window_start: int = 0
        self._window_count: int = 0

    def _reset_window(self, cycle: int) -> None:
        if cycle - self._window_start > self.policy.window_cycles:
            self._window_start = cycle
            self._window_count = 0

    def _in_cooldown(self, key: tuple[str, str], cycle: int) -> bool:
        last = self._last_utterance.get(key)
        return last is not None and cycle - last < self.policy.cooldown_cycles

    def _utterance(self, kind: str, entity: str, known: bool) -> str:
        """Deterministic, natural proactive remark (no LLM in the loop)."""
        if kind == "presence.entered":
            if entity:
                return f"Hey {entity} — good to see you." if known else "Hey — you're new to me. I'm Novi."
            return "Hey — good to see you."
        if kind == "presence.left":
            return f"{entity} headed out." if entity else "Someone just left."
        if kind == "scene.changed":
            return f"I noticed {entity} moved." if entity else "Something in the room changed."
        if kind == "identity.recognized":
            return f"Oh, it's you, {entity}." if entity else "Oh — I know you."
        if kind == "identity.auto_enrolled":
            return "Hey — you're new to me. I'm Novi. What's your name?"
        if kind == "hearing.anomaly":
            return "That sound was odd — did you hear it?"
        if kind == "person.holding":
            return f"Nice — you've got your {entity}." if entity else "I see you've got something in your hand."
        if kind == "object.novel":
            return f"Ooh — you've got a new {entity}. What is it?" if entity else "Ooh — something new in your hand. What is it?"
        if kind == "object.recognized":
            return f"I see your {entity}." if entity else "I see that object."
        return "Something caught my attention."

    def evaluate(
        self,
        events: Iterable[dict[str, Any]],
        *,
        cycle: int,
        known_entities: Iterable[str] = (),
        present_entities: Iterable[str] = (),
    ) -> CandidateInitiative | None:
        """Return at most one candidate for this cycle, or None to stay silent.

        ``known_entities`` are entities Novi remembers (identity bindings +
        knowledge-graph entities); ``present_entities`` are what perception
        currently sees. Both are lower-cased for matching.
        """
        self._reset_window(cycle)
        if self._window_count >= self.policy.max_per_window:
            return None
        known = {str(e).strip().lower() for e in known_entities if str(e).strip()}
        present = {str(e).strip().lower() for e in present_entities if str(e).strip()}
        for event in events:
            kind = str(event.get("kind") or "").strip().lower()
            if kind not in _EVENT_AFFORDANCE:
                continue
            prefer_object = kind in ("person.holding", "object.novel", "object.recognized")
            entity = _entity_of(event, prefer=("object",) if prefer_object else ())
            key = (kind, entity.lower())
            if self._in_cooldown(key, cycle):
                continue
            if kind == "presence.entered":
                reason = f"presence_entered:known={entity.lower() in known}"
            elif kind == "presence.left":
                if entity and entity.lower() not in present:
                    reason = f"presence_left:remembered={entity.lower() in known}"
                else:
                    continue
            elif kind == "scene.changed":
                novelty = _novelty_of(event)
                if novelty < self.policy.novelty_threshold:
                    continue
                reason = f"scene_changed:novelty={novelty:.2f}"
            elif kind == "identity.recognized":
                reason = f"identity_recognized:known={entity.lower() in known}"
            elif kind == "identity.auto_enrolled":
                reason = f"identity_auto_enrolled:known={entity.lower() in known}"
            elif kind == "hearing.anomaly":
                novelty = _novelty_of(event)
                if novelty < self.policy.novelty_threshold:
                    continue
                reason = f"hearing_anomaly:novelty={novelty:.2f}"
            elif kind == "object.novel":
                novelty = _novelty_of(event)
                if novelty < self.policy.novelty_threshold:
                    continue
                reason = f"object_novel:novelty={novelty:.2f}"
            elif kind == "person.holding":
                reason = f"person_holding:object_known={entity.lower() in known}"
            elif kind == "object.recognized":
                reason = f"object_recognized:known={entity.lower() in known}"
            else:  # pragma: no cover - guarded by the affordance membership above
                continue
            self._last_utterance[key] = cycle
            self._window_count += 1
            known_flag = entity.lower() in known
            return CandidateInitiative(
                kind=kind,
                entity=entity,
                text=self._utterance(kind, entity, known_flag),
                reason=reason,
                affordance=_EVENT_AFFORDANCE[kind],
                source_event=event,
            )
        return None
