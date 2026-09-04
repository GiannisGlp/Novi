"""Plan 03 Phase 9: deterministic response critic + repair.

``critique_draft`` scores a draft against the Step 9.2 dimensions that
are computable without a judge model; ``repair`` re-renders once under
stricter constraints; ``safety_fallback`` is the Step 9.4 last resort
(answer from verified facts → concise clarification → admitted
uncertainty — never fabricated confidence).

Deterministic, socket-free, stdlib-only. Bounded to one repair pass so
critic loops can never wedge the reply path.
"""

from __future__ import annotations

from novi.brain.conversation.conversation_state import (
    ContextPacket,
    CriticVerdict,
    ResponsePlan,
)
from novi.brain.conversation.response_planner import render_deterministic

_GENERIC_FILLER = [
    "that sounds interesting",
    "i understand",
    "tell me more",
    "that's interesting",
    "great question",
]

_META_TALK = [
    "according to the conversation history",
    "my context manager indicates",
    "the system says",
    "i have retrieved memory",
    "as an ai language model",
]

_CAPABILITY_CLAIMS = [
    "i just saw",
    "i can see right now",
    "i'll move",
    "i'll pick that up",
    "i remember everything",
]


def _score_repetition(draft: str, last_novi: str) -> float:
    if not draft.strip() or not last_novi.strip():
        return 1.0
    a = set(draft.lower().split())
    b = set(last_novi.lower().split())
    if not a or not b:
        return 1.0
    overlap = len(a & b) / max(len(a), len(b))
    return round(max(0.0, 1.0 - overlap), 3)


def _contains_any(text: str, phrases: list[str]) -> str | None:
    lowered = text.lower()
    return next((p for p in phrases if p in lowered), None)


def critique_draft(*, draft: str, packet: ContextPacket, plan: ResponsePlan,
                   last_novi: str = "") -> CriticVerdict:
    """Score the draft; list failed dimensions; propose repair (Step 9.2)."""
    text = draft or ""
    scores: dict[str, float] = {}
    failed: list[str] = []

    # Grounding: required evidence present, or the plan admits uncertainty.
    required = [r.lower() for r in plan.required_evidence if r]
    if required:
        hit = any(r in text.lower() for r in required)
        scores["grounding"] = 1.0 if hit else 0.0
    else:
        scores["grounding"] = 0.0 if not text.strip() else 0.8
    if scores["grounding"] < 0.5 and plan.goal not in (
            "ADMIT_UNCERTAINTY", "ASK_CLARIFICATION", "ACKNOWLEDGE",
            "CONTINUE_SOCIAL_CONVERSATION", "REASSURE", "CORRECT", "REMEMBER"):
        failed.append("grounding")

    # Non-repetition against the previous Novi turn.
    scores["non_repetition"] = _score_repetition(text, last_novi)
    if scores["non_repetition"] < 0.5:
        failed.append("non_repetition")

    # Naturalness: no filler-only or meta-talk replies.
    filler = _contains_any(text, _GENERIC_FILLER)
    meta = _contains_any(text, _META_TALK)
    scores["naturalness"] = 0.2 if (filler and len(text.split()) <= 12) or meta else 0.9
    if scores["naturalness"] < 0.5:
        failed.append("naturalness")

    # Contradiction safety: never restate a just-corrected error.
    correction = (packet.anchor.recent_correction or "").lower()
    scores["contradiction_safety"] = 1.0
    if correction and correction in text.lower() and plan.goal != "CORRECT":
        scores["contradiction_safety"] = 0.0
        failed.append("contradiction_safety")

    # Capability honesty: no claimed perception/action without evidence.
    claim = _contains_any(text, _CAPABILITY_CLAIMS)
    world_ok = bool(packet.world_context)
    scores["capability_honesty"] = 1.0 if (claim is None or world_ok) else 0.0
    if scores["capability_honesty"] < 0.5:
        failed.append("capability_honesty")

    # Context relevance + intent match are structural: the plan derives
    # from the packet, so a rendered draft inherits them unless repaired
    # away from the plan (checked by callers, default pass here).
    scores["context_relevance"] = 1.0
    scores["intent_match"] = 1.0

    needs_repair = bool(failed)
    instruction = ""
    if needs_repair:
        instruction = ("Re-render under stricter constraints: "
                       f"failed=[{', '.join(failed)}]; keep it short, "
                       "name the entity, use only verified packet facts.")
    return CriticVerdict(scores=scores, failed=failed,
                         repair_instruction=instruction,
                         needs_repair=needs_repair)


def repair(*, draft: str, packet: ContextPacket, plan: ResponsePlan,
           verdict: CriticVerdict, last_novi: str = "") -> str:
    """One bounded repair pass: tighten constraints and re-render."""
    tightened = ResponsePlan(
        goal=plan.goal,
        must_include=list(plan.must_include),
        may_include=list(plan.may_include),
        must_not_include=list(plan.must_not_include) + [
            "generic filler", "meta-talk", "repetition",
        ],
        required_evidence=list(plan.required_evidence),
        uncertainty_statement=plan.uncertainty_statement,
        emotional_style=plan.emotional_style,
        desired_length="short",
        question_allowed=plan.question_allowed,
        reason=f"repair of [{', '.join(verdict.failed)}]",
    )
    return render_deterministic(tightened, packet)


def safety_fallback(*, packet: ContextPacket, reason: str) -> str:
    """Step 9.4: verified facts → clarification → admitted uncertainty."""
    memory = next((str(m.get("content", "")).strip()
                   for m in packet.relevant_memories
                   if str(m.get("content", "")).strip()), "")
    if memory:
        return memory.rstrip(".") + "."
    entities = list(dict.fromkeys(packet.resolved_entities.values()))
    if packet.intent is not None and packet.intent.needs_clarification and entities:
        return f"Which one do you mean — {entities[0]}?"
    _ = reason
    return "I'm not sure I have that right — could you say a bit more?"
