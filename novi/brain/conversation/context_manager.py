"""Plan 03 Phase 4 — context manager (the central quality component).

Builds the smallest useful context set (Step 4.5 ``ContextPacket``) from
bounded sources (Step 4.1), ranked by the plan's ``context_score`` signals
(Step 4.2), trimmed by per-source budgets so memory can never crowd out the
actual conversation (Step 4.3), with every injected fact labeled by
``FactClass`` (Step 4.4).

Reuse, not duplication: world/perception facts come from the existing
``context_assembler.ContextAssembler``; memories come from
``memory_selector`` on top of ``DurableMemoryStore.retrieve_ranked``;
preferences come from the ``LearnedPreferences`` lexicon store; the packet
assembly is recorded on the existing ``DecisionTrace`` ring when available.
Deterministic, socket-free, stdlib-only.
"""

from __future__ import annotations

import contextlib
from dataclasses import replace
from typing import Any

from novi.brain.conversation.conversation_state import (
    ContextPacket,
    ConversationAnchor,
    FactClass,
)
from novi.brain.conversation.memory_selector import (
    build_memory_query,
    missing_memory_verdict,
    select_memories,
)

# Step 4.2 signal weights (documented constants; the plan expects these to be
# calibrated from real evaluation data — see Phase 12/14 replay evidence).
W_ENTITY_MATCH = 3.0
W_TOPIC_MATCH = 2.0
W_INTENT_MATCH = 1.5
W_RECENCY = 1.0
W_IMPORTANCE = 1.0
W_CONFIDENCE = 1.0
P_CONTRADICTION = 3.0
P_STALENESS = 1.5
P_DUPLICATION = 2.0

# Step 4.3 per-source budgets. Memory is deliberately capped at or below the
# history budget so retrieval can never crowd out the actual conversation.
MAX_HISTORY_ITEMS = 6
MAX_MEMORIES = 4
MAX_WORLD_FACTS = 4
MAX_GOALS = 3
MAX_PREFERENCES = 3
MAX_RELATIONSHIPS = 3
MAX_CORRECTIONS = 2
MAX_CONSTRAINTS = 4
MAX_UNCERTAINTY = 4
MAX_REQUIREMENTS = 4

MEMORY_INTENTS = frozenset({"MEMORY_QUERY", "MEMORY_UPDATE", "CORRECTION", "REFLECTION"})
GOAL_INTENTS = frozenset({"PLANNING", "TASK_REQUEST", "RECOMMENDATION", "COMPARISON"})
IDENTITY_INTENTS = frozenset({"IDENTITY_QUERY", "PERCEPTION_QUERY", "OBSERVATION_QUERY"})

_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "of", "at", "by", "for", "with",
    "about", "into", "to", "from", "in", "on", "is", "are", "was", "were",
    "be", "been", "being", "it", "its", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "our", "their", "what", "which", "who", "how",
    "when", "where", "why", "do", "does", "did", "can", "could", "should",
    "would", "there", "here", "so", "as", "no", "yes", "not", "just",
})


def _content_tokens(text: str) -> set[str]:
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in text or "").split()
            if t and t not in _STOPWORDS}


def context_score(text: str, *, query_entities: tuple[str, ...] = (),
                  query_topic: str = "", intent_match: float = 0.0,
                  recency: float = 0.0, importance: float = 0.5,
                  confidence: float = 0.5, contradicted: bool = False,
                  stale: bool = False, duplicate: bool = False) -> float:
    """Step 4.2 combined relevance score (higher = more relevant)."""
    lowered = (text or "").lower()
    entity_match = 1.0 if any(e and e.lower() in lowered for e in query_entities) else 0.0
    topic_tokens = _content_tokens(query_topic)
    text_tokens = _content_tokens(text)
    topic_match = (len(topic_tokens & text_tokens) / len(topic_tokens)) if topic_tokens else 0.0
    return (
        W_ENTITY_MATCH * entity_match
        + W_TOPIC_MATCH * topic_match
        + W_INTENT_MATCH * intent_match
        + W_RECENCY * recency
        + W_IMPORTANCE * importance
        + W_CONFIDENCE * confidence
        - P_CONTRADICTION * contradicted
        - P_STALENESS * stale
        - P_DUPLICATION * duplicate
    )


def label_fact(source_kind: str, confidence: float = 0.5,
               superseded: bool = False) -> FactClass:
    """Step 4.4: label every injected fact with its epistemic class."""
    if superseded:
        return FactClass.HISTORICAL_STATE
    if confidence < 0.35:
        return FactClass.UNCERTAIN
    kind = (source_kind or "").lower()
    if kind in ("memory", "relationship"):
        return FactClass.MEMORY
    if kind == "preference":
        return FactClass.PREFERENCE
    if kind in ("user_turn", "utterance", "correction"):
        return FactClass.USER_STATED_FACT
    if kind in ("observation", "perception"):
        return FactClass.OBSERVED_FACT
    if kind in ("world_state", "identity", "goal", "summary"):
        return FactClass.HISTORICAL_STATE if kind == "summary" else FactClass.CURRENT_STATE
    if kind == "hypothesis":
        return FactClass.HYPOTHESIS
    if kind in ("social", "emotional"):
        return FactClass.INFERENCE
    return FactClass.INFERENCE


def _intent_affinity(intent_label: str, source_kind: str) -> float:
    if source_kind == "memory" and intent_label in MEMORY_INTENTS:
        return 1.0
    if source_kind == "goal" and intent_label in GOAL_INTENTS:
        return 1.0
    if source_kind == "identity" and intent_label in IDENTITY_INTENTS:
        return 1.0
    return 0.0


def _rank_keep(scored: list[tuple[float, Any]], budget: int) -> list[Any]:
    ranked = sorted(scored, key=lambda pair: -pair[0])
    return [item for _, item in ranked[:max(0, budget)]]


def _gather_history(state: Any, query_entities: tuple[str, ...],
                    query_topic: str) -> list[str]:
    turns = list(getattr(state, "recent_turns", []) or [])
    scored: list[tuple[float, str]] = []
    seen: set[str] = set()
    total = max(1, len(turns))
    for index, turn in enumerate(turns):
        user = str(turn.get("user", "")) if isinstance(turn, dict) else str(turn)
        novi = str(turn.get("novi", "")) if isinstance(turn, dict) else ""
        line = f"user: {user}" + (f" / novi: {novi}" if novi else "")
        normalized = " ".join(line.lower().split())
        duplicate = normalized in seen
        seen.add(normalized)
        scored.append((context_score(
            line, query_entities=query_entities, query_topic=query_topic,
            recency=(index + 1) / total, duplicate=duplicate), line))
    # Chronological order restored after ranking so the packet reads as dialogue.
    kept = _rank_keep(scored, MAX_HISTORY_ITEMS)
    kept.sort(key=lambda line: next((i for i, (_, ln) in enumerate(scored) if ln == line), 0))
    summary = (getattr(state, "conversation_summary", "") or "").strip()
    if summary:
        kept = [f"summary: {summary[:300]}"] + kept
        del kept[MAX_HISTORY_ITEMS:]
    return kept


def _gather_world(text: str, entities: tuple[str, ...], brain: Any) -> list[dict[str, Any]]:
    world = getattr(brain, "unified_world", None)
    if world is None:
        return []
    try:
        from novi.brain.context_assembler import ContextAssembler, ContextRequest
        package = ContextAssembler().assemble(
            world, ContextRequest(task_type="dialogue", utterance=text,
                                  referenced_labels=tuple(entities)))
    except Exception:
        return []
    facts: list[dict[str, Any]] = []
    for item in package.items:
        data = item.data if isinstance(item.data, dict) else {"value": str(item.data)}
        if item.kind == "memory":
            kind = "memory"
        elif item.kind == "event":
            kind = "utterance"
        elif item.epistemic_status == "OBSERVED":
            kind = "observation"
        else:
            kind = "world_state"
        entry = {
            "text": str(data)[:300],
            "source": item.source or item.layer,
            "confidence": round(item.confidence, 4),
            "fact_class": label_fact(kind, item.confidence).value,
        }
        # Keep entity labels on the fact so the response planner can name
        # what was observed without parsing the serialized payload.
        labels = data.get("labels") if isinstance(data, dict) else None
        if labels:
            entry["labels"] = [str(label)[:60] for label in list(labels)[:4]]
            entry["entity_id"] = str(data.get("entity_id", ""))[:80]
        facts.append(entry)
        if len(facts) >= MAX_WORLD_FACTS * 2:
            break
    return facts[:MAX_WORLD_FACTS]


def _gather_identity(brain: Any) -> dict[str, Any]:
    identity = getattr(brain, "identity", None)
    if identity is None:
        return {}
    with contextlib.suppress(Exception):
        snapshot = identity.snapshot() or {}
        person = ""
        confidence = 0.0
        with contextlib.suppress(Exception):
            belief = identity.identity_for("person")
            if belief is not None:
                person = getattr(belief, "name", "") or ""
                confidence = float(getattr(belief, "confidence", 0.0) or 0.0)
        return {"person": person, "confidence": round(confidence, 4),
                "fact_class": FactClass.CURRENT_STATE.value,
                "presence": snapshot.get("presence", {})}
    return {}


def _gather_social(brain: Any) -> dict[str, Any]:
    social = getattr(brain, "social", None)
    if social is None:
        return {}
    for method in ("snapshot", "to_dict"):
        with contextlib.suppress(Exception):
            data = getattr(social, method)()
            if isinstance(data, dict) and data:
                return {k: data[k] for k in list(data)[:8]}
    return {}


def _gather_emotional(brain: Any, state: Any) -> dict[str, Any]:
    for attr in ("affective_state", "affect", "emotion"):
        with contextlib.suppress(Exception):
            node = getattr(brain, attr, None)
            if node is not None and hasattr(node, "snapshot"):
                data = node.snapshot()
                if isinstance(data, dict) and data:
                    out = {k: data[k] for k in list(data)[:8]}
                    out.setdefault("fact_class", FactClass.INFERENCE.value)
                    return out
    anchor_emotion = ""
    with contextlib.suppress(Exception):
        anchor_emotion = (getattr(state, "anchor", None).emotional_context or "")
    return {"tone": anchor_emotion or "neutral",
            "fact_class": FactClass.INFERENCE.value}


def _gather_goals(state: Any, brain: Any) -> list[str]:
    goals: list[str] = []
    user_goal = (getattr(state, "user_goal", "") or "").strip()
    if user_goal:
        goals.append(user_goal[:200])
    with contextlib.suppress(Exception):
        controller = getattr(brain, "goals", None)
        if controller is not None and controller.has_active:
            active = controller.active
            describe = getattr(active, "describe", None) or getattr(active, "snapshot", None)
            if callable(describe):
                goals.append(str(describe())[:200])
            else:
                goals.append(str(active)[:200])
    return goals[:MAX_GOALS]


def _gather_constraints(brain: Any) -> list[str]:
    constraints = ["default privacy scope: withhold private/restricted memories",
                   "ground claims in packet facts only; do not invent memories"]
    with contextlib.suppress(Exception):
        prefs = getattr(brain, "preferences", None)
        snapshot = prefs.snapshot() if prefs is not None else []
        if isinstance(snapshot, dict):
            snapshot = list(snapshot.values())
        for pref in list(snapshot or [])[:MAX_PREFERENCES]:
            if not isinstance(pref, dict) or not pref.get("active", True):
                continue
            constraints.append(
                f"preference ({pref.get('kind', 'style')}): {pref.get('value', '')}"[:160])
            if len(constraints) >= MAX_CONSTRAINTS:
                break
    return constraints[:MAX_CONSTRAINTS]


def _record_trace(brain: Any, text: str, intent: Any,
                  citations: list[dict[str, Any]], goals: list[str]) -> None:
    with contextlib.suppress(Exception):
        recorder = getattr(brain, "decision_traces", None)
        if recorder is None or not hasattr(recorder, "new_trace"):
            return
        trace = recorder.new_trace(cycle_id=int(getattr(brain, "_cycle", 0) or 0),
                                   input_event=(text or "")[:160])
        trace.retrieved_memories = [c.get("memory_id", "") for c in citations if c.get("memory_id")]
        trace.goals = list(goals)
        trace.dialogue_act = getattr(intent, "dialogue_act", "") or ""
        trace.dialogue_reason = getattr(intent, "reason", "") or ""


def build_packet(text: str, state: Any, intent: Any, referents: Any,
                 brain: Any) -> ContextPacket:
    """Assemble the smallest useful context set for one turn (Steps 4.1–4.5)."""
    query_entities = tuple(getattr(state, "active_entities", []) or [])
    resolutions = dict(getattr(referents, "resolutions", {}) or {})
    for resolved in resolutions.values():
        if resolved and resolved not in query_entities:
            query_entities = query_entities + (resolved,)
    # The entity the reply must stay grounded on is what THIS turn refers to,
    # not the recency-ordered workspace head: a freshly-taught place ("Porto")
    # must not become "stay grounded on Porto" for a car-interior question.
    focus_entities = [str(v) for v in resolutions.values() if str(v)]
    if not focus_entities:
        anchor_entity = (getattr(getattr(state, "anchor", None),
                                  "active_entity", "") or "").strip()
        if anchor_entity:
            focus_entities = [anchor_entity]
    query_topic = (getattr(state, "topic", "") or "").strip()
    intent_label = (getattr(intent, "intent", "") or "").strip()

    history = _gather_history(state, query_entities, query_topic)

    memory_query = build_memory_query(text, state, intent, referents, brain)
    citations: list[dict[str, Any]] = []
    with contextlib.suppress(Exception):
        store = getattr(brain, "memory", None)
        if store is not None and hasattr(store, "retrieve_ranked"):
            mem_cap = min(MAX_MEMORIES, len(history)) if history else MAX_MEMORIES
            citations = select_memories(store, memory_query, limit=mem_cap)
    memories: list[dict[str, Any]] = []
    for citation in citations:
        entry = dict(citation)
        entry["fact_class"] = label_fact("memory", entry.get("confidence", 0.5)).value
        memories.append(entry)

    world_facts = _gather_world(text, query_entities, brain)
    identity = _gather_identity(brain)
    social = _gather_social(brain)
    with contextlib.suppress(Exception):
        store = getattr(brain, "memory", None)
        relationships = (store.load_relationships() or []) if store is not None else []
        if relationships:
            social = {**social, "relationships": relationships[:MAX_RELATIONSHIPS]}
    emotional = _gather_emotional(brain, state)
    goals = _gather_goals(state, brain)
    constraints = _gather_constraints(brain)

    uncertainty: list[str] = []
    confidence = float(getattr(intent, "confidence", 0.0) or 0.0)
    if confidence < 0.6:
        uncertainty.append(f"low intent confidence ({confidence:.2f}) for {intent_label or 'unknown'}")
    for ambiguous in (getattr(referents, "ambiguous", []) or [])[:2]:
        uncertainty.append(f"ambiguous referent: {ambiguous}")
    if getattr(intent, "needs_clarification", False):
        uncertainty.append("interpreter requested clarification")
    if intent_label == "MEMORY_QUERY" and not memories:
        verdict = missing_memory_verdict(memory_query.text, [])
        uncertainty.append(f"no reliable memory found — say so honestly ('{verdict.statement}')")

    requirements: list[str] = []
    if intent_label:
        requirements.append(f"address intent {intent_label}")
    if focus_entities:
        requirements.append(f"stay grounded on {focus_entities[0][:80]}")
    with contextlib.suppress(Exception):
        corrections = getattr(brain, "corrections", None)
        records = corrections.snapshot() if corrections is not None else []
        if isinstance(records, dict):
            records = list(records.values())
        for record in list(records or [])[-MAX_CORRECTIONS:]:
            requirements.append(f"honor correction: {record}"[:160])
            if len(requirements) >= MAX_REQUIREMENTS:
                break
    if getattr(referents, "ambiguous", []):
        requirements.append("ask a short specific clarification only if ambiguity changes the answer")

    anchor = getattr(state, "anchor", None)
    packet = ContextPacket(
        current_turn=text or "",
        intent=intent,
        resolved_entities=resolutions,
        active_entities=[str(e) for e in (query_entities or [])][:8],
        anchor=replace(anchor) if anchor is not None else ConversationAnchor(),
        relevant_history=history,
        relevant_memories=memories,
        world_context=world_facts,
        identity_context=identity,
        social_context=social,
        emotional_context=emotional,
        active_goals=goals,
        constraints=constraints[:MAX_CONSTRAINTS],
        uncertainty=uncertainty[:MAX_UNCERTAINTY],
        response_requirements=requirements[:MAX_REQUIREMENTS],
    )
    _record_trace(brain, text or "", intent, citations, goals)
    return packet


__all__ = [
    "MAX_CONSTRAINTS",
    "MAX_CORRECTIONS",
    "MAX_GOALS",
    "MAX_HISTORY_ITEMS",
    "MAX_MEMORIES",
    "MAX_PREFERENCES",
    "MAX_RELATIONSHIPS",
    "MAX_REQUIREMENTS",
    "MAX_UNCERTAINTY",
    "MAX_WORLD_FACTS",
    "P_CONTRADICTION",
    "P_DUPLICATION",
    "P_STALENESS",
    "W_CONFIDENCE",
    "W_ENTITY_MATCH",
    "W_IMPORTANCE",
    "W_INTENT_MATCH",
    "W_RECENCY",
    "W_TOPIC_MATCH",
    "build_packet",
    "context_score",
    "label_fact",
]
