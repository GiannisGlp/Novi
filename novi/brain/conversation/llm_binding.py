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
        lines.append(f"- response goal: {getattr(plan, 'goal', '?')}")
        must = [str(m)[:80] for m in (getattr(plan, "must_include", []) or [])[:3] if m]
        must_not = [str(m)[:80] for m in (getattr(plan, "must_not_include", []) or [])[:3] if m]
        if must:
            lines.append(f"- must include: {'; '.join(must)}")
        if must_not:
            lines.append(f"- must NOT include: {'; '.join(must_not)}")
        uncertainty = str(getattr(plan, "uncertainty_statement", "") or "").strip()
        if uncertainty:
            lines.append(f"- uncertainty: {uncertainty[:160]}")
        packet_uncertainty = getattr(packet, "uncertainty", []) if packet is not None else []
        for item in list(packet_uncertainty or [])[:2]:
            lines.append(f"- uncertainty: {str(item)[:160]}")
        style = str(getattr(plan, "emotional_style", "") or "").strip()
        if style:
            lines.append(f"- emotional style: {style[:80]}")
        if getattr(plan, "question_allowed", False) is False:
            lines.append("- do not ask a clarification question; answer directly")
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
    "conversation_state_payload",
    "render_conversation_block",
    "route_for_turn",
]
