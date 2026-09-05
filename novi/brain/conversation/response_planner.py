"""Plan 03 Phase 7: response planning + deterministic rendering.

``plan_response`` decides what a reply must accomplish BEFORE any
wording exists (Step 7.1/7.2); ``render_deterministic`` realizes the
plan as honest text from verified packet facts only. The renderer never
invents facts, capabilities, or observations — when evidence is absent
it names the entity, admits the gap, or asks the planned clarification
(Step 9.4 fallback semantics shared with the critic).

Deterministic, socket-free, stdlib-only. LLM realization consumes the
same ``ResponsePlan`` (must/may/must-not + requirements travel in the
prompt); this module owns the plan, not the model.
"""

from __future__ import annotations

from typing import Any

from novi.brain.conversation.conversation_state import (
    ContextPacket,
    ResponsePlan,
)

# Intents answered directly when the packet carries evidence.
_DIRECT_INTENTS = frozenset({
    "INFORMATION_REQUEST",
    "EXPLANATION_REQUEST",
    "MEMORY_QUERY",
    "CONFIRMATION",
    "IDENTITY_QUERY",
    "OBSERVATION_QUERY",
    "PERCEPTION_QUERY",
})

# Intents that compare, recommend, or explain.
_REASONING_INTENTS = frozenset({
    "COMPARISON",
    "RECOMMENDATION",
    "OPINION_REQUEST",
    "PLANNING",
    "REFLECTION",
})


def packet_entities(packet: ContextPacket) -> list[str]:
    """Resolved entities plus the anchor entity (deduped, ordered).

    The anchor carries continuity when the current turn names nothing new
    ("What about the range?" after "Model Y") — plans and renders must see
    it or follow-ups go entity-blind.
    """
    ordered = list(packet.resolved_entities.values())
    anchor = (packet.anchor.active_entity or "").strip()
    if anchor and anchor.lower() not in {e.lower() for e in ordered}:
        ordered.append(anchor)
    topic = (packet.anchor.topic or "").strip()
    if topic and topic.lower() not in {e.lower() for e in ordered}:
        ordered.append(topic)
    return ordered


def plan_response(packet: ContextPacket) -> ResponsePlan:
    """Select the communicative goal and content constraints (Steps 7.1–7.4)."""
    intent = packet.intent
    name = (intent.intent if intent else "").upper()
    needs_clar = bool(intent and intent.needs_clarification)
    conf = float(intent.confidence) if intent else 0.0
    entities = packet_entities(packet)

    if name == "GREETING":
        return ResponsePlan(
            goal="ACKNOWLEDGE", desired_length="short",
            may_include=["warmth"], must_not_include=["meta-talk"],
            emotional_style="warm",
            reason="greeting: brief natural acknowledgement, never a question",
        )
    if name == "FAREWELL":
        return ResponsePlan(
            goal="ACKNOWLEDGE", desired_length="short",
            emotional_style="warm", reason="farewell: brief warm close",
        )
    if name in ("CORRECTION", "DISCONFIRMATION"):
        return ResponsePlan(
            goal="CORRECT", desired_length="short",
            must_include=["acknowledgement of the correction"],
            must_not_include=["defense of the prior interpretation"],
            reason="correction: update context, never defend the error",
        )
    if name == "MEMORY_UPDATE":
        return ResponsePlan(
            goal="REMEMBER", desired_length="short",
            must_include=["confirmation of what was stored"],
            reason="memory update: confirm storage briefly",
        )
    if needs_clar and conf < 0.60:
        candidates = sorted(set(packet_entities(packet)))
        return ResponsePlan(
            goal="ASK_CLARIFICATION", desired_length="short",
            question_allowed=True,
            must_include=candidates[:3] or ["the specific options"],
            must_not_include=["generic filler"],
            reason="material ambiguity below confidence: short specific question",
        )
    if name in ("PERCEPTION_QUERY", "OBSERVATION_QUERY"):
        # Only substantive perception answers: the packet may carry the
        # user's own utterance echoed as world context (source stt) —
        # that is not an observation and must not license scene claims.
        # _gather_world entries carry serialized payloads under "text",
        # so text counts as content here (echo sources already excluded).
        substantive = [w for w in packet.world_context
                       if isinstance(w, dict)
                       and str(w.get("source", "")).lower() not in (
                           "stt", "chat", "transcript", "user", "dialogue")
                       and (w.get("detections") or w.get("objects")
                            or w.get("people") or w.get("observation")
                            or w.get("content") or w.get("labels")
                            or w.get("text"))]
        if substantive:
            return ResponsePlan(
                goal="ANSWER_DIRECTLY", desired_length="short",
                must_include=list(packet.resolved_entities.values())[:2],
                required_evidence=[_world_phrase(w) for w in substantive[:2]],
                question_allowed=False,
                reason="fresh perception available: answer from it",
            )
        return ResponsePlan(
            goal="ADMIT_UNCERTAINTY", desired_length="short",
            uncertainty_statement="I can't reliably see that right now.",
            question_allowed=False,
            reason="no fresh perception: vision honesty, never hallucinate",
        )
    if name == "TASK_REQUEST":
        return ResponsePlan(
            goal="ADMIT_UNCERTAINTY", desired_length="short",
            uncertainty_statement=("I can't carry out physical actions myself, "
                                   "but I can help you plan it."),
            question_allowed=False,
            reason="action honesty: distinguish capability from intention",
        )
    # Step 7.3: unresolved referents make recommendations/comparisons
    # unanswerable — ask before guessing (C-011/C-131 semantics).
    if packet.ambiguous_referents and name in (
            "RECOMMENDATION", "COMPARISON", "INFORMATION_REQUEST"):
        candidates = sorted(set(packet_entities(packet)))
        return ResponsePlan(
            goal="ASK_CLARIFICATION", desired_length="short",
            question_allowed=True,
            must_include=candidates[:3] or ["the specific options"],
            reason="ambiguous referents: short specific question",
        )
    if name == "SUMMARIZATION":
        return ResponsePlan(
            goal="SUMMARIZE", desired_length="short",
            must_include=entities[:2],
            question_allowed=False,
            reason="summary request: recap entities and turn count from state",
        )
    if name == "RECOMMENDATION":
        evidence = [m.get("content", "") for m in packet.relevant_memories
                    if m.get("content")]
        if evidence:
            return ResponsePlan(
                goal="RECOMMEND", desired_length="short",
                must_include=list(packet.resolved_entities.values())[:2],
                required_evidence=evidence[:3],
                must_not_include=["generic filler"],
                question_allowed=False,
                reason="recommendation grounded in recalled preferences",
            )
        return ResponsePlan(
            goal="ADMIT_UNCERTAINTY", desired_length="short",
            uncertainty_statement=("I don't have a reliable basis "
                                   "for a recommendation."),
            question_allowed=False,
            reason="no preference evidence: admit, never invent taste",
        )
    if name in _DIRECT_INTENTS:
        evidence = [m.get("content", "") for m in packet.relevant_memories
                    if m.get("content")]
        # Memory questions are answered from memory evidence only: world
        # facts or bare entities never license a "remembered" answer.
        answerable = evidence if name == "MEMORY_QUERY" else (
            evidence or packet.world_context or entities)
        if answerable:
            return ResponsePlan(
                goal="ANSWER_DIRECTLY", desired_length="short",
                must_include=entities[:2],
                required_evidence=evidence[:3],
                must_not_include=["generic filler"],
                question_allowed=False,
                reason="answerable from packet evidence: answer, do not ask",
            )
        return ResponsePlan(
            goal="ADMIT_UNCERTAINTY", desired_length="short",
            uncertainty_statement="I don't have a reliable memory of that.",
            question_allowed=False,
            reason="no packet evidence: admit the gap, never fabricate",
        )
    if name in _REASONING_INTENTS:
        return ResponsePlan(
            goal="EXPLAIN" if name != "COMPARISON" else "COMPARE",
            desired_length="medium",
            must_include=entities[:2],
            must_not_include=["generic filler"],
            question_allowed=False,
            reason="reasoning intent: grounded explanation from packet facts",
        )
    if name in ("EMOTIONAL_SUPPORT", "REASSURANCE"):
        return ResponsePlan(
            goal="REASSURE", desired_length="short",
            emotional_style="warm",
            must_not_include=["canned therapy language", "generic filler"],
            reason="emotional intent: acknowledge feeling, stay genuine",
        )
    if name in ("JOKE/HUMOR", "SOCIAL_CHAT"):
        return ResponsePlan(
            goal="CONTINUE_SOCIAL_CONVERSATION", desired_length="short",
            emotional_style="warm",
            must_not_include=["generic filler"],
            reason="social intent: brief natural continuation",
        )
    return ResponsePlan(
        goal="ACKNOWLEDGE", desired_length="short",
        reason=f"unmapped intent {name or 'none'}: safe acknowledgement",
    )


def _world_phrase(fact: dict[str, Any]) -> str:
    """Name what a world-context fact observes, for evidence and voicing.

    Entity labels win ("cup"); otherwise fall back to the observation /
    content text. Never returns the raw serialized payload.
    """
    labels = [str(label).strip() for label in (fact.get("labels") or [])
              if str(label).strip()]
    if labels:
        return ", ".join(labels[:3])[:120]
    for key in ("observation", "content"):
        value = str(fact.get(key) or "").strip()
        if value:
            return value[:200]
    text = str(fact.get("text") or "").strip()
    return text[:200]


def _with_article(phrase: str) -> str:
    """Add an indefinite article to a bare single-word observation label."""
    word = phrase.strip()
    if " " in word or not word or not word[0].isalpha() or not word[0].islower():
        return word
    return ("an " if word[0] in "aeiou" else "a ") + word


def _memory_answer(packet: ContextPacket) -> str:
    for mem in packet.relevant_memories:
        content = str(mem.get("content", "")).strip()
        if content:
            return content.rstrip(".") + "."
    return ""


def _select_memory(packet: ContextPacket) -> tuple[str, str]:
    """Choose the memory answer and its kind.

    Durable preferences outrank raw recent claims about the same topic
    (a learned preference supersedes the utterances that taught it);
    two distinct live claims signal a conflict the reply must name
    (C-133) instead of silently picking one. A supported cross-session
    routine (C-122) annotates a confident preference/claim answer as
    the user's usual — it never voices uncertainty admissions or
    conflicts, and unsupported patterns never reach this point.
    """
    from novi.brain.conversation.thread_store import ROUTINE_PREFIX

    prefs: list[str] = []
    claims: list[str] = []
    others: list[str] = []
    routine_seen = False
    for mem in packet.relevant_memories:
        if not isinstance(mem, dict):
            continue
        content = str(mem.get("content", "")).strip()
        if not content:
            continue
        if mem.get("memory_type") == "routine":
            routine_seen = True
        elif mem.get("fact_class") == "PREFERENCE":
            prefs.append(content)
        elif mem.get("memory_type") == "recent_claim":
            claims.append(content)
        else:
            others.append(content)
    if prefs:
        answer, kind = prefs[0].rstrip(".") + ".", "preference"
    else:
        unique_claims = list(dict.fromkeys(claims))
        if len(unique_claims) >= 2:
            latest = unique_claims[-1].rstrip(".")
            quoted = " and ".join(f"'{c.rstrip('.')}'" for c in unique_claims)
            return (f"You mentioned both {quoted} — going by the latest, "
                    f"'{latest}'.", "conflict")
        if unique_claims:
            answer, kind = unique_claims[0].rstrip(".") + ".", "claim"
        elif others:
            answer, kind = others[0].rstrip(".") + ".", "memory"
        else:
            return "", ""
    if routine_seen and kind in ("preference", "claim"):
        return f"{ROUTINE_PREFIX}{answer}", "routine"
    return answer, kind


def render_deterministic(plan: ResponsePlan, packet: ContextPacket) -> str:
    """Realize the plan from verified packet facts only (never fabricate)."""
    entities = packet_entities(packet)
    entity = entities[0] if entities else ""

    if plan.goal == "ASK_CLARIFICATION":
        options = [o for o in plan.must_include if o != "the specific options"]
        if len(options) >= 2:
            return f"Do you mean {options[0]} or {options[1]}?"
        if entity:
            return f"Which {entity} do you mean?"
        return "Could you say a little more about which one you mean?"

    if plan.goal == "ADMIT_UNCERTAINTY":
        return plan.uncertainty_statement or "I don't have a reliable memory of that."

    if plan.goal in ("ANSWER_DIRECTLY", "EXPLAIN", "COMPARE", "RECOMMEND"):
        memory, kind = _select_memory(packet)
        if not memory:
            # Perception answers (plan §6.3): voice observed world facts
            # directly. The evidence must re-derive from the packet's world
            # context — never from memory content (a routine annotation or
            # preference must never be voiced as something seen).
            phrases = {_world_phrase(w) for w in packet.world_context
                       if isinstance(w, dict)}
            perception = [str(e).strip() for e in plan.required_evidence
                          if str(e).strip() and str(e).strip() in phrases]
            if perception:
                return f"I can see {_with_article(perception[0])}" + (
                    f" and {_with_article(perception[1])}"
                    if len(perception) > 1 else "") + "."
        if memory:
            if kind == "conflict":
                return memory
            # Situate the memory under the entity only when they relate;
            # prefixing an unrelated anchor is MEMORY_IRRELEVANT ("About
            # Porto: you prefer dark interiors").
            entity_words = {w for w in entity.lower().split() if len(w) > 3}
            related = entity and (
                entity.lower() in memory.lower()
                or any(w in memory.lower() for w in entity_words))
            if related:
                return f"About {entity}: {memory}"
            return memory[0].upper() + memory[1:] if memory else memory
        if entity:
            return (f"I don't have verified details on {entity} handy — "
                    f"want me to look into it?")
        return "I don't have verified facts on that yet."

    if plan.goal == "CORRECT":
        from novi.brain.conversation.conversation_state import (
            mention_candidates,
            preferred_correction_entity,
        )

        target = preferred_correction_entity(
            mention_candidates(packet.current_turn), packet.current_turn)
        if target:
            return f"Got it — {target} from here on."
        if entity:
            return f"Got it — {entity} from here on."
        return "Got it — I'll go with the corrected version."

    if plan.goal == "REMEMBER":
        return "Noted — I'll remember that."

    if plan.goal in ("ACKNOWLEDGE", "CONTINUE_SOCIAL_CONVERSATION", "REASSURE"):
        topic = packet.anchor.topic
        if topic:
            return f"Yeah — {topic}."
        return "Hey, I'm here."

    if plan.goal == "SUMMARIZE":
        history = packet.relevant_history or []
        if entity and history:
            return (f"We've been talking about {entity} "
                    f"({len(history)} recent turns).")
        if entity:
            return f"We've been talking about {entity}."
        return "We've covered a few things so far."

    return "Okay."
