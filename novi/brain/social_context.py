"""Short-lived social context (plan 22, Phase 7).

A derived, *observable-probabilistic* description of the current social
situation — never a claim about private mental states.

Bad:  "Vano is angry."
Good: "speech tempo increased, volume increased → interaction tone may be
       tense, confidence 0.58" (plan §11).

SocialContext is derived per cycle from perception + person model +
conversation state and feeds dialogue policy (Phase 10) and initiative
scoring (Phase 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class SocialContext:
    addressee: str = ""
    relationship: str = "unknown"
    interaction_phase: str = "none"  # none | greeting | active | winding_down | departed
    attention_to_novi: float = 0.0
    user_availability: str = "unknown"  # available | busy | unknown
    user_engagement: float = 0.0
    conversation_temperature: str = "unknown"  # calm | neutral | tense | unknown
    temperature_confidence: float = 0.0
    interruptibility: float = 1.0  # 1 = safe to interrupt, 0 = never
    familiarity: float = 0.0
    social_opportunity: float = 0.0
    cues: list[dict[str, Any]] = field(default_factory=list)  # observable evidence

    def snapshot(self) -> dict[str, Any]:
        return {
            "addressee": self.addressee,
            "relationship": self.relationship,
            "interaction_phase": self.interaction_phase,
            "attention_to_novi": round(self.attention_to_novi, 3),
            "user_availability": self.user_availability,
            "user_engagement": round(self.user_engagement, 3),
            "conversation_temperature": self.conversation_temperature,
            "temperature_confidence": round(self.temperature_confidence, 3),
            "interruptibility": round(self.interruptibility, 3),
            "familiarity": round(self.familiarity, 3),
            "social_opportunity": round(self.social_opportunity, 3),
            "cues": list(self.cues),
        }


@dataclass
class SocialEvidence:
    """Observable inputs the builder may use (all optional)."""

    person_name: str = ""
    familiarity: float = 0.0  # person-model confidence when known
    relationship: str = "unknown"
    last_user_utterance_cycle: int = -1
    current_cycle: int = 0
    user_speaking: bool = False  # ASR/VAD says the user is mid-turn
    novi_speaking: bool = False  # speaking lease held
    interaction_count: int = 0
    recent_utterances: int = 0  # user utterances in the recent window
    speech_tempo_ratio: float | None = None  # >1 = faster than baseline
    speech_volume_ratio: float | None = None  # >1 = louder than baseline
    person_present: bool = False


class SocialContextBuilder:
    """Derive SocialContext from observable evidence (deterministic)."""

    def build(self, evidence: SocialEvidence) -> SocialContext:
        ctx = SocialContext()
        ctx.addressee = evidence.person_name
        ctx.relationship = evidence.relationship or "unknown"
        ctx.familiarity = _clamp01(evidence.familiarity)
        ctx.cues = []

        # ---- interaction phase ----
        if not evidence.person_present:
            ctx.interaction_phase = "departed"
        elif evidence.recent_utterances > 0:
            ctx.interaction_phase = "active"
        elif evidence.interaction_count > 0:
            ctx.interaction_phase = "greeting"
        # else "none"

        # ---- attention / engagement (observable proxies) ----
        if evidence.user_speaking or evidence.recent_utterances > 0:
            ctx.attention_to_novi = _clamp01(0.5 + 0.1 * evidence.recent_utterances)
            ctx.user_engagement = _clamp01(0.4 + 0.15 * evidence.recent_utterances)
        else:
            ctx.attention_to_novi = 0.2 if evidence.person_present else 0.0
            ctx.user_engagement = 0.15 if evidence.person_present else 0.0

        # ---- availability ----
        if evidence.user_speaking or evidence.recent_utterances > 0:
            ctx.user_availability = "busy"
        elif evidence.person_present:
            ctx.user_availability = "available"
        else:
            ctx.user_availability = "unknown"

        # ---- temperature: ONLY from observable cues, with confidence ----
        if evidence.speech_tempo_ratio is not None or evidence.speech_volume_ratio is not None:
            tempo = evidence.speech_tempo_ratio or 1.0
            volume = evidence.speech_volume_ratio or 1.0
            tension = 0.0
            cue_count = 0
            if tempo > 1.3:
                tension += 0.6
                ctx.cues.append({"cue": "speech_tempo_increased", "value": round(tempo, 2), "weight": 0.6})
                cue_count += 1
            if volume > 1.2:
                tension += 0.5
                ctx.cues.append({"cue": "speech_volume_increased", "value": round(volume, 2), "weight": 0.5})
                cue_count += 1
            if tension > 0:
                ctx.conversation_temperature = "tense"
                ctx.temperature_confidence = _clamp01(0.4 + 0.18 * cue_count)
            else:
                ctx.conversation_temperature = "calm"
                ctx.temperature_confidence = 0.5
        # else temperature stays "unknown" — no mind-reading without cues

        # ---- interruptibility ----
        ctx.interruptibility = 0.0 if evidence.user_speaking else 1.0
        if evidence.novi_speaking:
            ctx.interruptibility = min(ctx.interruptibility, 0.1)
        if evidence.recent_utterances > 0 and ctx.interruptibility > 0:
            ctx.interruptibility = _clamp01(ctx.interruptibility * 0.7)

        # ---- social opportunity: engaged + available + interruptible ----
        if not evidence.person_present:
            ctx.social_opportunity = 0.0  # nobody here — no opportunity
        else:
            ctx.social_opportunity = _clamp01(
                ctx.user_engagement * 0.5
                + (1.0 if ctx.user_availability == "available" else 0.2 if ctx.user_availability == "busy" else 0.0) * 0.3
                + ctx.interruptibility * 0.2
            )
        return ctx
