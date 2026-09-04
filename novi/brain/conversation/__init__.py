"""Plan 03 conversation package: conversation as a first-class process."""

from novi.brain.conversation.conversation_state import (
    MAX_ACTIVE_ENTITIES,
    MAX_RECENT_TURNS,
    ContextPacket,
    ConversationAnchor,
    ConversationState,
    CriticVerdict,
    FactClass,
    IntentResult,
    ReferentResult,
    ResponsePlan,
    TopicTransition,
    classify_topic_transition,
)

__all__ = [
    "MAX_ACTIVE_ENTITIES",
    "MAX_RECENT_TURNS",
    "ContextPacket",
    "ConversationAnchor",
    "ConversationState",
    "CriticVerdict",
    "FactClass",
    "IntentResult",
    "ReferentResult",
    "ResponsePlan",
    "TopicTransition",
    "classify_topic_transition",
]


def __getattr__(name: str):
    # Heavy submodules import lazily so importing the package never pulls
    # the world model, store, or planner graphs transitively.
    if name in ("classify_intent",):
        from novi.brain.conversation.intent import classify_intent

        return classify_intent
    if name in ("resolve_referents",):
        from novi.brain.conversation.referent_resolution import resolve_referents

        return resolve_referents
    if name in ("build_packet",):
        from novi.brain.conversation.context_manager import build_packet

        return build_packet
    if name in ("plan_response", "render_deterministic"):
        from novi.brain.conversation import response_planner as _planner

        return getattr(_planner, name)
    if name in ("critique_draft", "repair", "safety_fallback"):
        from novi.brain.conversation import response_critic as _critic

        return getattr(_critic, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

