"""Dialogue policy — the social decision layer (plan 22, Phase 10).

``DialoguePolicy.decide(context) -> DialogueDecision`` selects the
communicative act from conversation state, world state, person identity,
social context, working memory, retrieved memories, goals, predictions,
attention, salience, prospective memory, recent speech, speaking lease and
initiative budget (plan §14 inputs).

Outputs (plan §14): SILENCE / RESPOND / ASK / CLARIFY / ACKNOWLEDGE /
COMMENT / INFORM / SUGGEST / WARN / FOLLOW_UP / GREETING / FAREWELL /
INITIATE / CONTINUE / INTERRUPT / REPAIR.

Every proactive decision carries an explicit ``why_now`` / ``why_this_person``
/ ``why_this_topic`` / ``why_this_verbosity`` / ``why_speak`` (Task 10.2) for
observability and evaluation. Deterministic, rule-based, explainable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DialogueAct(str, Enum):
    SILENCE = "SILENCE"
    RESPOND = "RESPOND"
    ASK = "ASK"
    CLARIFY = "CLARIFY"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    COMMENT = "COMMENT"
    INFORM = "INFORM"
    SUGGEST = "SUGGEST"
    WARN = "WARN"
    FOLLOW_UP = "FOLLOW_UP"
    GREETING = "GREETING"
    FAREWELL = "FAREWELL"
    INITIATE = "INITIATE"
    CONTINUE = "CONTINUE"
    INTERRUPT = "INTERRUPT"
    REPAIR = "REPAIR"


@dataclass
class DialogueContext:
    """Everything the policy is allowed to see (plan §14 inputs)."""

    # conversation
    user_message: str = ""
    has_user_message: bool = False
    is_greeting: bool = False
    is_farewell: bool = False
    is_question: bool = False
    is_thanks: bool = False
    is_correction: bool = False
    clarification_needed: bool = False
    unresolved_questions: list[str] = field(default_factory=list)
    last_novi_act: str = ""
    speaking_lease_held: bool = False
    # world
    person_present: bool = False
    person_entered: bool = False
    person_left: bool = False
    salient_events: list[dict[str, Any]] = field(default_factory=list)
    safety_event: bool = False
    # identity / social
    addressee: str = ""
    addressee_known: bool = False
    social_opportunity: float = 0.0
    user_engagement: float = 0.0
    interruptibility: float = 1.0
    recently_greeted: bool = False
    # cognition / memory
    open_threads: list[str] = field(default_factory=list)
    commitments_due: list[str] = field(default_factory=list)
    active_goal: str = ""
    prediction_failed: bool = False
    initiative_budget_available: bool = True


@dataclass
class DialogueDecision:
    act: DialogueAct = DialogueAct.SILENCE
    target: str = ""
    topic: str = ""
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    urgency: float = 0.0
    interruption_cost: float = 0.0
    expected_value: float = 0.0
    verbosity: str = "short"  # short | medium | long
    tone: str = "conversational"
    why_now: str = ""
    why_this_person: str = ""
    why_this_topic: str = ""
    why_this_verbosity: str = ""
    why_speak: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "act": self.act.value,
            "target": self.target,
            "topic": self.topic,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "confidence": round(self.confidence, 3),
            "urgency": round(self.urgency, 3),
            "interruption_cost": round(self.interruption_cost, 3),
            "expected_value": round(self.expected_value, 3),
            "verbosity": self.verbosity,
            "tone": self.tone,
            "why_now": self.why_now,
            "why_this_person": self.why_this_person,
            "why_this_topic": self.why_this_topic,
            "why_this_verbosity": self.why_this_verbosity,
            "why_speak": self.why_speak,
        }


class DialoguePolicy:
    """Rule-based communicative-act selection (the social decision layer)."""

    def decide(self, ctx: DialogueContext) -> DialogueDecision:
        # 1. Safety always wins (plan §2.9 / Gate H7).
        if ctx.safety_event:
            return DialogueDecision(
                act=DialogueAct.WARN, urgency=1.0, confidence=0.95,
                reason="safety_event", evidence=["safety_event"],
                why_now="safety overrides ordinary social suppression",
                why_this_person=ctx.addressee or "everyone",
                why_this_topic="safety", why_this_verbosity="short",
                why_speak="a safety event must be spoken, never suppressed",
            )
        # 2. While Novi is composing, nothing proactive interrupts (plan §11.3).
        if ctx.speaking_lease_held and not ctx.has_user_message:
            return DialogueDecision(
                act=DialogueAct.SILENCE, reason="composing_hold",
                why_now="a reply is already being composed",
                why_this_person="", why_this_topic="", why_this_verbosity="",
                why_speak="proactive candidates queue, never interrupt",
            )
        # 3. Direct user message → reactive acts.
        if ctx.has_user_message:
            return self._reactive(ctx)
        # 4. No message: proactive acts.
        return self._proactive(ctx)

    def _reactive(self, ctx: DialogueContext) -> DialogueDecision:
        if ctx.is_farewell:
            return DialogueDecision(
                act=DialogueAct.FAREWELL, target=ctx.addressee, confidence=0.9,
                reason="farewell", why_now="user is leaving",
                why_this_person=ctx.addressee, why_this_topic="",
                why_this_verbosity="short", why_speak="acknowledge the goodbye",
            )
        if ctx.is_greeting:
            return DialogueDecision(
                act=DialogueAct.GREETING, target=ctx.addressee, confidence=0.9,
                reason="greeting", why_now="user greeted Novi",
                why_this_person=ctx.addressee, why_this_topic="",
                why_this_verbosity="short", why_speak="greet back naturally",
            )
        if ctx.is_correction:
            return DialogueDecision(
                act=DialogueAct.REPAIR, target=ctx.addressee, confidence=0.85,
                reason="correction", evidence=["user_correction"],
                why_now="user corrected a previous claim",
                why_this_person=ctx.addressee, why_this_topic="",
                why_this_verbosity="short",
                why_speak="acknowledge and record the correction",
            )
        if ctx.clarification_needed:
            return DialogueDecision(
                act=DialogueAct.CLARIFY, target=ctx.addressee, confidence=0.8,
                reason="ambiguous_reference",
                evidence=ctx.unresolved_questions[:2],
                why_now="the reference is ambiguous and a physical action is at stake",
                why_this_person=ctx.addressee, why_this_topic="",
                why_this_verbosity="short",
                why_speak="never silently guess when ambiguity matters",
            )
        if ctx.is_thanks:
            return DialogueDecision(
                act=DialogueAct.ACKNOWLEDGE, target=ctx.addressee, confidence=0.9,
                reason="thanks", why_now="user thanked Novi",
                why_this_person=ctx.addressee, why_this_topic="",
                why_this_verbosity="short", why_speak="acknowledge briefly",
            )
        if ctx.is_question:
            return DialogueDecision(
                act=DialogueAct.RESPOND, target=ctx.addressee, confidence=0.8,
                reason="question", verbosity="medium",
                why_now="user asked something", why_this_person=ctx.addressee,
                why_this_topic=ctx.user_message[:60],
                why_this_verbosity="medium — answers need a little room",
                why_speak="answer when addressed",
            )
        return DialogueDecision(
            act=DialogueAct.RESPOND, target=ctx.addressee, confidence=0.75,
            reason="addressed", verbosity="short",
            why_now="user addressed Novi", why_this_person=ctx.addressee,
            why_this_topic=ctx.user_message[:60],
            why_this_verbosity="short — conversation, not report",
            why_speak="answer when addressed",
        )

    def _proactive(self, ctx: DialogueContext) -> DialogueDecision:
        # commitments due are high-value follow-ups (Phase 6)
        if ctx.commitments_due:
            return DialogueDecision(
                act=DialogueAct.INITIATE, target=ctx.addressee,
                topic=ctx.commitments_due[0], confidence=0.9,
                urgency=0.6, expected_value=0.85,
                reason="commitment_due",
                evidence=list(ctx.commitments_due),
                why_now="an open commitment became due",
                why_this_person=ctx.addressee,
                why_this_topic=ctx.commitments_due[0],
                why_this_verbosity="short",
                why_speak="follow up on what was promised",
            )
        if ctx.person_entered and not ctx.recently_greeted:
            opportunity_ok = ctx.social_opportunity >= 0.35 and ctx.interruptibility >= 0.5
            return DialogueDecision(
                act=DialogueAct.GREETING if opportunity_ok else DialogueAct.SILENCE,
                target=ctx.addressee, confidence=0.85, urgency=0.4,
                expected_value=0.7,
                reason="person_entered" if opportunity_ok else "person_entered_low_opportunity",
                why_now="a person entered the room",
                why_this_person=ctx.addressee or "unknown person",
                why_this_topic="", why_this_verbosity="short",
                why_speak="a greeting is appropriate when the person is available",
            )
        if ctx.person_left and ctx.addressee_known:
            return DialogueDecision(
                act=DialogueAct.FAREWELL, target=ctx.addressee, confidence=0.7,
                urgency=0.3, expected_value=0.5, reason="person_left",
                why_now="a known person left", why_this_person=ctx.addressee,
                why_this_topic="", why_this_verbosity="short",
                why_speak="a brief farewell for a familiar person",
            )
        if ctx.open_threads and ctx.social_opportunity >= 0.5 and ctx.initiative_budget_available:
            return DialogueDecision(
                act=DialogueAct.CONTINUE, target=ctx.addressee,
                topic=ctx.open_threads[0], confidence=0.75, urgency=0.35,
                expected_value=0.8, reason="unfinished_thread",
                evidence=list(ctx.open_threads[:2]),
                why_now="an unresolved thread exists and the user is available",
                why_this_person=ctx.addressee,
                why_this_topic=ctx.open_threads[0],
                why_this_verbosity="short",
                why_speak="conversation is driven by continuity, not only questions",
            )
        if ctx.prediction_failed:
            return DialogueDecision(
                act=DialogueAct.COMMENT, target=ctx.addressee, confidence=0.6,
                urgency=0.5, expected_value=0.55, reason="prediction_failed",
                why_now="a prediction failed significantly",
                why_this_person=ctx.addressee, why_this_topic="",
                why_this_verbosity="short",
                why_speak="significant prediction failures are worth noting",
            )
        # salient events: comment only when the anti-narration gate agrees
        speakable = [
            e for e in ctx.salient_events
            if e.get("kind") in {"object.disappeared", "object.moved", "object.novel", "task.completed", "hearing.anomaly", "identity.recognized", "presence.entered"}
        ]
        if speakable and ctx.interruptibility >= 0.6 and ctx.initiative_budget_available:
            evt = speakable[0]
            return DialogueDecision(
                act=DialogueAct.COMMENT, target=ctx.addressee, confidence=0.65,
                urgency=0.4, expected_value=0.6, reason=f"salient_event:{evt.get('kind')}",
                topic=evt.get("entity", ""),
                evidence=[evt.get("entity", "")],
                why_now=f"a salient event worth mentioning ({evt.get('kind')})",
                why_this_person=ctx.addressee or "whoever is present",
                why_this_topic=evt.get("entity", ""),
                why_this_verbosity="short",
                why_speak="the event passes the worth-saying gate",
            )
        return DialogueDecision(
            act=DialogueAct.SILENCE, reason="nothing_worth_saying",
            why_now="no message, no due commitment, no high-value event",
            why_this_person="", why_this_topic="", why_this_verbosity="",
            why_speak="silence is a first-class act (plan §2.6)",
        )
