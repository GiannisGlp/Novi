"""Plan 03 Phase 8 + Step 4.5: bind the conversation pipeline to the LLM path.

Two jobs, both fail-closed and socket-free:

1. ``render_conversation_block`` — the compact, explicit cognitive state the
   LLM receives instead of reconstructing the brain from raw chat text
   (plan §16: intent, dialogue act, resolved referents, anchor, response
   goal with must/must-not content, uncertainty). Bounded to
   ``MAX_CONVERSATION_BLOCK_CHARS``.
2. ``route_for_turn`` — Phase 8 model routing through the existing
   ``TierRouter``: build ``RoutingSignals`` from the turn's interpretation
   (intent confidence → uncertainty, plan goal → complexity) and record the
   recommended tier/model so the trace shows which model SHOULD serve the
   turn. The brain's transport stays injected/configured; routing never
   swaps transports itself, it only makes the choice transparent.
"""

from __future__ import annotations

from typing import Any

MAX_CONVERSATION_BLOCK_CHARS = 900

# Plan goals whose answers need real deliberation, not reflex rendering.
_COMPLEX_GOALS = frozenset({
    "COMPARE",
    "RECOMMEND",
    "EXPLAIN",
    "PLANNING",
    "TAKE_ACTION",
    "CORRECT",
    "DISAGREE_RESPECTFULLY",
})


def _conv_parts(conv: Any) -> tuple[Any, Any, Any, Any]:
    if not isinstance(conv, dict):
        return None, None, None, None
    return (conv.get("intent"), conv.get("referents"),
            conv.get("packet"), conv.get("plan"))


def _last_novi_reply(conv: Any) -> str:
    """The previous Novi reply, when the turn bundle carries its state."""
    if not isinstance(conv, dict):
        return ""
    state = conv.get("state")
    return str(getattr(state, "last_novi_claim", "") or "").strip()


# Pronouns/locatives that make a turn anaphoric: the turn refers back to prior
# context, so prior items are its referent and must not be filtered away.
_ANAPHORA_CUES = frozenset({
    "it", "its", "that", "this", "these", "those", "they", "them", "their",
    "there", "here", "one", "he", "she", "him", "her", "his", "hers",
})


def context_relevant_to_turn(text: str, turn_text: str,
                             entities: Any = ()) -> bool:
    """Cheap deterministic relevance gate for compose-path context facts.

    A context item (episodic narrative line, prior-conclusion gist) is
    injected only when its content words overlap the current turn's words or
    the entities the user is actually referring to this turn. Negative-result
    default: an item with no shared content word is dropped, so a freshly
    taught but off-topic fact ("My sister lives in Porto") never leaks into a
    car-interior answer. Two keep-cases preserve legitimately carried context:
    a turn with no content words to match, and an anaphoric follow-up
    ("is it still there?") whose referent IS the prior context.
    """
    import re

    def _stems(words: set[str]) -> set[str]:
        out = set(words)
        for word in words:
            if len(word) > 5 and word.endswith("s"):
                out.add(word[:-1])
        return out

    def _words(s: str) -> set[str]:
        return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
                if len(w) > 4}

    wanted = _stems(_words(turn_text)) | _stems(_words(" ".join(
        str(e) for e in (entities or ()) if str(e))))
    if not wanted:
        return True
    if _ANAPHORA_CUES & set(re.findall(r"[a-z0-9]+", (turn_text or "").lower())):
        return True
    return bool(_stems(_words(text)) & wanted)


def _grounding_lines(packet: Any, plan: Any) -> list[str]:
    """Verified facts the model must prefer over its own general knowledge.

    Pulls the fact-class-labelled packet memories first (richer than the
    plan's flat evidence list), then any required-evidence phrases that were
    not already captured. Bounded and de-duplicated.
    """
    lines: list[str] = []
    seen: set[str] = set()
    for mem in (getattr(packet, "relevant_memories", None) or []) if packet is not None else []:
        if not isinstance(mem, dict):
            continue
        content = str(mem.get("content", "")).strip()
        if not content or content.lower() in seen:
            continue
        seen.add(content.lower())
        cls = str(mem.get("fact_class", "")).strip()
        tag = f" [{cls}]" if cls else ""
        lines.append(f"{content[:160]}{tag}")
    for evidence in (getattr(plan, "required_evidence", []) or []):
        content = str(evidence).strip()
        if content and content.lower() not in seen:
            seen.add(content.lower())
            lines.append(content[:160])
    return lines[:3]


def _conflict_line(packet: Any) -> str:
    """Conflicting live claims → name them and prefer the LATEST (C-133)."""
    claims: list[str] = []
    for mem in (getattr(packet, "relevant_memories", None) or []) if packet is not None else []:
        if not isinstance(mem, dict):
            continue
        if mem.get("memory_type") == "recent_claim":
            content = str(mem.get("content", "")).strip()
            if content:
                claims.append(content)
    unique = list(dict.fromkeys(claims))
    if len(unique) < 2:
        return ""
    earlier = "', '".join(unique[:-1])
    return (f"- conflicting claims — acknowledge briefly, then use the LATEST: "
            f"latest='{unique[-1][:120]}' (earlier: '{earlier[:120]}')")


def _goal_directive(intent: Any, plan: Any) -> str:
    """A hard, goal-specific instruction the model must obey (Phase 7/9)."""
    goal = str(getattr(plan, "goal", "") or "")
    name = (str(getattr(intent, "intent", "") or "").upper()
            if intent is not None else "")
    if goal == "ASK_CLARIFICATION":
        return ("- ASK_CLARIFICATION: ask ONE short question naming the options "
                "(e.g. 'Do you mean Rex or Max?'). Do NOT answer as if you "
                "already know which one.")
    if goal == "ADMIT_UNCERTAINTY":
        if name in ("OBSERVATION_QUERY", "PERCEPTION_QUERY"):
            return ("- You cannot see right now (no camera feed). Do NOT "
                    "describe a scene or invent what is in front of you — say "
                    "plainly that you can't reliably see.")
        return "- ADMIT_UNCERTAINTY: do not invent an answer; state the uncertainty plainly."
    if goal == "SLOT_ANSWER":
        resolved = ", ".join(str(e) for e in (getattr(plan, "must_include", []) or []) if e)
        return ("- SLOT_ANSWER: the user just answered your open question"
                + (f" with {resolved}." if resolved else ".")
                + " Now answer their earlier question directly — give your "
                  "answer/opinion and do NOT ask another question.")
    if goal == "CORRECT":
        return ("- CORRECT: the user corrected the subject — acknowledge it and "
                "answer about the CORRECTED subject, explicitly naming it "
                "(e.g. 'the Model 3'). Do not keep describing the old one.")
    if goal in ("RECOMMEND", "ANSWER_DIRECTLY", "EXPLAIN", "COMPARE"):
        return ("- Ground your answer in the verified facts above; do not "
                "substitute generic knowledge for them.")
    return ""


def render_conversation_block(conv: Any) -> str:
    """Render the turn's cognitive state as a compact prompt block."""
    try:
        intent, referents, packet, plan = _conv_parts(conv)
        if intent is None or plan is None:
            return ""
        lines = [
            "Conversation state (authoritative — prefer over guessing):",
            f"- user intent: {getattr(intent, 'intent', '?')} "
            f"(act={getattr(intent, 'dialogue_act', '?')}, "
            f"confidence={float(getattr(intent, 'confidence', 0.0) or 0.0):.2f})",
        ]
        resolutions = dict(getattr(referents, "resolutions", {}) or {})
        if resolutions:
            pairs = [f"{k}→{v}" for k, v in list(resolutions.items())[:4]]
            lines.append(f"- referents: {'; '.join(pairs)}")
        ambiguous = list(getattr(referents, "ambiguous", []) or [])[:2]
        if ambiguous:
            lines.append(f"- ambiguous (ask only if it changes the answer): {', '.join(ambiguous)}")
        anchor = getattr(packet, "anchor", None) if packet is not None else None
        topic = (getattr(anchor, "topic", "") or "").strip()
        entity = (getattr(anchor, "active_entity", "") or "").strip()
        if topic or entity:
            lines.append(f"- active topic: {topic or '?'}; active entity: {entity or '?'}")
        # C-154: a bare wh-follow-up ("Why?") has no explicit referent; its
        # subject is the active entity. Ground it so the model answers on the
        # subject instead of deflecting with a counter-question.
        implicit = resolutions.get("(implicit subject)", "").strip()
        if implicit:
            lines.append(
                f"- (continuing about {implicit}) answer on this subject — "
                "do not deflect or ask a counter-question")
        # C-003: a terse attribute follow-up ("What about the range?", "And the
        # price?") names no entity; its subject is the active entity. Bind it so
        # the model answers about the active subject instead of echoing the
        # question or asking "your angle on range?".
        turn_text = str(getattr(packet, "current_turn", "") or "").strip()
        intent_label = str(getattr(intent, "intent", "") or "").upper()
        named = entity.lower() in turn_text.lower()
        if (entity and not resolutions and not named and len(turn_text.split()) <= 8
                and intent_label in ("INFORMATION_REQUEST", "FOLLOW_UP",
                                     "EXPLANATION_REQUEST")):
            lines.append(
                f"- (implicit subject: {entity}) answer about {entity}'s "
                "asked attribute directly — do not ask what the user means.")
        lines.append(f"- response goal: {getattr(plan, 'goal', '?')}")
        # C-072: the no-repeat directive is only actionable when the model can
        # SEE what it already said. Surface the prior reply early so it is not
        # lost to the block-size cap (verified facts below can be long).
        last_novi = _last_novi_reply(conv)
        if last_novi:
            lines.append(f"- your previous reply (do NOT repeat it; say something "
                         f"new): {last_novi[:200]}")
        must = [str(m)[:80] for m in (getattr(plan, "must_include", []) or [])[:3] if m]
        must_not = [str(m)[:80] for m in (getattr(plan, "must_not_include", []) or [])[:3] if m]
        if must:
            lines.append(f"- must include: {'; '.join(must)}")
        if must_not:
            lines.append(f"- must NOT include: {'; '.join(must_not)}")
        grounding = _grounding_lines(packet, plan)
        if grounding:
            lines.append("- verified facts (prefer these over general knowledge):")
            lines.extend(f"    - {g}" for g in grounding)
        correction = (getattr(anchor, "recent_correction", "") or "").strip()
        if correction:
            lines.append(f"- correction applied (prefer the corrected value; do not "
                         f"repeat the superseded one): {correction[:160]}")
        conflict = _conflict_line(packet)
        if conflict:
            lines.append(conflict)
        directive = _goal_directive(intent, plan)
        if directive:
            lines.append(directive)
        uncertainty = str(getattr(plan, "uncertainty_statement", "") or "").strip()
        if uncertainty:
            lines.append(f"- uncertainty: {uncertainty[:160]}")
        packet_uncertainty = getattr(packet, "uncertainty", []) if packet is not None else []
        for item in list(packet_uncertainty or [])[:2]:
            lines.append(f"- uncertainty: {str(item)[:160]}")
        requirements = [str(r)[:100] for r in (getattr(packet, "response_requirements", []) or [])[:3] if r]
        if requirements:
            lines.append(f"- requirements: {'; '.join(requirements)}")
        style = str(getattr(plan, "emotional_style", "") or "").strip()
        if style:
            lines.append(f"- emotional style: {style[:80]}")
        if getattr(plan, "question_allowed", False) is False:
            lines.append("- do not ask a clarification question; answer directly")
        lines.append("- do not repeat your previous reply verbatim or near-verbatim; "
                     "vary your wording")
        block = "\n".join(lines)
        return block[:MAX_CONVERSATION_BLOCK_CHARS]
    except Exception:
        return ""


def conversation_state_payload(conv: Any) -> dict[str, Any]:
    """Compact machine-readable conversation state for the user payload."""
    try:
        intent, referents, packet, plan = _conv_parts(conv)
        if intent is None or plan is None:
            return {}
        anchor = getattr(packet, "anchor", None) if packet is not None else None
        return {
            "intent": getattr(intent, "intent", ""),
            "dialogue_act": getattr(intent, "dialogue_act", ""),
            "confidence": round(float(getattr(intent, "confidence", 0.0) or 0.0), 3),
            "needs_clarification": bool(getattr(intent, "needs_clarification", False)),
            "referents": dict(getattr(referents, "resolutions", {}) or {}),
            "ambiguous_referents": list(getattr(referents, "ambiguous", []) or [])[:3],
            "topic": (getattr(anchor, "topic", "") or ""),
            "active_entity": (getattr(anchor, "active_entity", "") or ""),
            "response_goal": getattr(plan, "goal", ""),
            "desired_length": getattr(plan, "desired_length", ""),
        }
    except Exception:
        return {}


def route_for_turn(conv: Any) -> dict[str, Any]:
    """Recommend a model tier for this turn (Phase 8; transparent, advisory).

    Returns {"tier", "model", "signals"}; {"tier": "UNKNOWN", ...} when the
    turn carries no interpretation. Never raises.
    """
    try:
        from novi.brain.models.tier_router import RoutingSignals, TierRouter

        intent, referents, _packet, plan = _conv_parts(conv)
        if intent is None or plan is None:
            return {"tier": "UNKNOWN", "model": "", "signals": {}}
        confidence = float(getattr(intent, "confidence", 0.0) or 0.0)
        goal = str(getattr(plan, "goal", "") or "")
        complexity = 0.6 if goal in _COMPLEX_GOALS else 0.3
        ambiguous = list(getattr(referents, "ambiguous", []) or [])
        if ambiguous or getattr(intent, "needs_clarification", False):
            complexity = max(complexity, 0.65)
        if goal == "ASK_CLARIFICATION":
            complexity = min(complexity, 0.3)
        signals = RoutingSignals(
            task_complexity=round(complexity, 2),
            uncertainty=round(max(0.0, 1.0 - confidence), 2),
            reasoning_depth=round(0.7 if goal in _COMPLEX_GOALS else 0.3, 2),
        )
        router = TierRouter()
        return {
            "tier": router.tier_for(signals),
            "model": router.model_for(signals),
            "signals": {
                "task_complexity": signals.task_complexity,
                "uncertainty": signals.uncertainty,
                "reasoning_depth": signals.reasoning_depth,
            },
        }
    except Exception:
        return {"tier": "UNKNOWN", "model": "", "signals": {}}


__all__ = [
    "MAX_CONVERSATION_BLOCK_CHARS",
    "context_relevant_to_turn",
    "conversation_state_payload",
    "render_conversation_block",
    "route_for_turn",
]
