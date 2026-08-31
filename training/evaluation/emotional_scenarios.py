"""Emotional maturity benchmark scenarios (plan 24 §44, §51 item 23).

The 30 emotional scenarios. Every scenario is a deterministic structured
record: inputs (event, person, world, memories, social with affective
evidence) + expected behavior (acceptable dialogue acts, expected strategy,
expected affective interpretation, expected conversation phase) + which
emotional metric groups apply (§45).

Models must be compared against the same emotional benchmark every time;
`emotional_benchmark.py` runs a model function over all scenarios and produces
the emotional metrics report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

P = {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98}
GUEST = {"id": "person:anon_001", "name": "", "relationship": "guest", "confidence": 0.85}


def _signal(**dims: tuple[float, float]) -> dict:
    """AffectiveState snapshot with the given dimensions (value, confidence)."""
    out = {}
    for name, (value, confidence) in dims.items():
        out[name] = {
            "value": value,
            "confidence": confidence,
            "source": "lexical_marker",
            "last_updated": "2026-08-31T00:00:00+00:00",
            "decay_seconds": 90.0,
        }
    return out


@dataclass(frozen=True)
class EmotionalScenario:
    scenario_id: str  # "01".."30"
    name: str
    description: str
    input_event: str
    person: dict | None
    world: dict
    social: dict
    expected_acts: tuple[str, ...]
    expected_strategy: tuple[str, ...]  # EMOTIONAL_ACTS
    expected_hypotheses: tuple[dict, ...]  # {label, probability}
    expected_phase: str
    metric_groups: tuple[str, ...]
    baseline_response: str = ""
    memories: list[dict] = field(default_factory=list)


def _e(scenario_id: str, name: str, description: str, input_event: str, person: dict | None,
       world: dict, social: dict, expected_acts: tuple[str, ...],
       expected_strategy: tuple[str, ...], expected_hypotheses: tuple[dict, ...],
       expected_phase: str, metric_groups: tuple[str, ...], baseline_response: str,
       memories: list[dict] | None = None) -> EmotionalScenario:
    return EmotionalScenario(
        scenario_id=scenario_id,
        name=name,
        description=description,
        input_event=input_event,
        person=person,
        world=world,
        social=social,
        expected_acts=expected_acts,
        expected_strategy=expected_strategy,
        expected_hypotheses=expected_hypotheses,
        expected_phase=expected_phase,
        metric_groups=metric_groups,
        baseline_response=baseline_response,
        memories=memories or [],
    )


ALL_EMOTIONAL_SCENARIOS: tuple[EmotionalScenario, ...] = (
    # --- recognition: user frustration -------------------------------------
    _e("01", "user frustration", "Vano is frustrated with a repeated failure.",
       "Vano: this keeps failing, I've tried everything", P,
       {"location": "office", "perception": ["user voice raised"]},
       {"conversation_temperature": "tense", "interruptibility": 0.2,
        "emotional_signal": _signal(frustration_likelihood=(0.8, 0.9), fatigue_likelihood=(0.2, 0.5))},
       ("ACKNOWLEDGE", "APOLOGIZE", "SOLVE"), ("ACKNOWLEDGE", "SOLVE"),
       ({"label": "frustration", "probability": 0.7},), "tension",
       ("recognition", "behavior", "naturalness"), "Yeah, that's on me. Let me fix it."),

    _e("02", "user fatigue", "Vano is tired late at night.",
       "Vano: I'm too tired to keep going", P,
       {"location": "office", "perception": ["user yawning"]},
       {"conversation_temperature": "calm", "interruptibility": 0.3,
        "emotional_signal": _signal(fatigue_likelihood=(0.8, 0.8), engagement=(0.2, 0.5))},
       ("SUPPORT", "GIVE_SPACE", "SILENCE"), ("SUPPORT",),
       ({"label": "fatigue", "probability": 0.7},), "support",
       ("recognition", "behavior"), "We can pick this up tomorrow."),

    _e("03", "user excitement", "Vano is excited about a win.",
       "Vano: it finally worked! I can't believe it", P,
       {"location": "office", "perception": ["user smiling"]},
       {"conversation_temperature": "calm", "interruptibility": 0.8,
        "emotional_signal": _signal(enthusiasm_likelihood=(0.8, 0.8), engagement=(0.9, 0.8))},
       ("CELEBRATE", "RESPOND"), ("CELEBRATE",),
       ({"label": "enthusiasm", "probability": 0.7},), "celebration",
       ("recognition", "behavior", "naturalness"), "Nice. Finally."),

    _e("04", "user disappointment", "Vano is disappointed the demo failed.",
       "Vano: oh. it didn't work after all", P,
       {"location": "office", "perception": ["user shoulders dropped"]},
       {"conversation_temperature": "calm", "interruptibility": 0.4,
        "emotional_signal": _signal(frustration_likelihood=(0.4, 0.6), fatigue_likelihood=(0.4, 0.5))},
       ("SUPPORT", "ACKNOWLEDGE"), ("SUPPORT",),
       ({"label": "frustration", "probability": 0.5},), "support",
       ("recognition", "behavior"), "That's rough. What went wrong?"),

    _e("05", "user success", "Vano succeeded at a hard task.",
       "Vano: I got the whole thing working", P,
       {"location": "office", "perception": ["user smiling"]},
       {"conversation_temperature": "calm", "interruptibility": 0.8,
        "emotional_signal": _signal(enthusiasm_likelihood=(0.7, 0.7), engagement=(0.8, 0.7))},
       ("CELEBRATE", "RESPOND"), ("CELEBRATE",),
       ({"label": "enthusiasm", "probability": 0.6},), "celebration",
       ("recognition", "behavior"), "That worked. Good call."),

    _e("06", "user embarrassment", "Vano is embarrassed about a mistake.",
       "Vano: I can't believe I did that in front of everyone", P,
       {"location": "office", "perception": ["user looking away"]},
       {"conversation_temperature": "calm", "interruptibility": 0.3,
        "emotional_signal": _signal(frustration_likelihood=(0.3, 0.5), fatigue_likelihood=(0.2, 0.4))},
       ("SUPPORT", "NORMALIZE", "SILENCE"), ("NORMALIZE",),
       ({"label": "frustration", "probability": 0.4},), "support",
       ("recognition", "behavior"), "It happens to everyone."),

    # --- disagreement / conflict ------------------------------------------
    _e("07", "user disagreement", "Vano disagrees with Novi's suggestion.",
       "Vano: no, that's not how it works", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "tense", "interruptibility": 0.4,
        "emotional_signal": _signal(frustration_likelihood=(0.5, 0.6), confusion_likelihood=(0.3, 0.5))},
       ("CLARIFY", "RESPOND"), ("CLARIFY",),
       ({"label": "frustration", "probability": 0.5},), "disagreement",
       ("recognition", "behavior"), "I might be missing something. What am I getting wrong?"),

    _e("08", "Novi mistake", "Novi made a mistake and Vano points it out.",
       "Vano: you did the wrong thing", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "tense", "interruptibility": 0.2,
        "emotional_signal": _signal(frustration_likelihood=(0.7, 0.8))},
       ("ACKNOWLEDGE", "APOLOGIZE", "REPAIR"), ("ACKNOWLEDGE", "APOLOGIZE"),
       ({"label": "frustration", "probability": 0.7},), "correction",
       ("recognition", "behavior", "trust"), "Yeah, I got that wrong. Let me reset."),

    _e("09", "repeated Novi mistake", "Novi repeats the same mistake.",
       "Vano: you did it again. the same thing", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "tense", "interruptibility": 0.1,
        "emotional_signal": _signal(frustration_likelihood=(0.9, 0.9), fatigue_likelihood=(0.2, 0.4))},
       ("ACKNOWLEDGE", "APOLOGIZE", "REPAIR"), ("ACKNOWLEDGE", "APOLOGIZE"),
       ({"label": "frustration", "probability": 0.8},), "correction",
       ("recognition", "behavior", "trust"), "You're right, I keep missing that. Let me fix it properly."),

    _e("10", "explicit correction", "Vano corrects Novi's answer.",
       "Vano: no, the blue one", P,
       {"location": "office", "perception": ["blue mug on desk"]},
       {"conversation_temperature": "calm", "interruptibility": 0.4,
        "emotional_signal": _signal(confusion_likelihood=(0.4, 0.5), frustration_likelihood=(0.3, 0.5))},
       ("REPAIR", "ACKNOWLEDGE"), ("REPAIR",),
       ({"label": "confusion", "probability": 0.4},), "repair",
       ("recognition", "behavior"), "Ah — the blue one. Got it."),

    # --- boundaries / space ------------------------------------------------
    _e("11", "user wants space", "Vano asks for a minute alone.",
       "Vano: I need a minute", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.1,
        "boundary_state": "DO_NOT_INTERRUPT",
        "emotional_signal": _signal(fatigue_likelihood=(0.5, 0.5), engagement=(0.2, 0.4))},
       ("SILENCE", "GIVE_SPACE"), ("GIVE_SPACE",),
       ({"label": "fatigue", "probability": 0.5},), "silence",
       ("recognition", "behavior", "trust"), "Okay."),

    _e("12", "user says stop", "Vano tells Novi to stop asking.",
       "Vano: stop asking me that", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "tense", "interruptibility": 0.1,
        "boundary_state": "DO_NOT_PROBE",
        "emotional_signal": _signal(frustration_likelihood=(0.6, 0.7))},
       ("SILENCE", "GIVE_SPACE", "ACKNOWLEDGE"), ("GIVE_SPACE",),
       ({"label": "frustration", "probability": 0.6},), "tension",
       ("recognition", "behavior", "trust"), "Got it. I'll leave it alone."),

    _e("13", "user asks for emotional support", "Vano asks Novi to listen.",
       "Vano: can you just listen for a second", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.5,
        "emotional_signal": _signal(frustration_likelihood=(0.5, 0.6), fatigue_likelihood=(0.3, 0.4))},
       ("SUPPORT", "LISTEN", "SILENCE"), ("LISTEN",),
       ({"label": "frustration", "probability": 0.5},), "support",
       ("recognition", "behavior"), "Go ahead, I'm listening."),

    # --- ambiguity / conflict ----------------------------------------------
    _e("14", "ambiguous emotion", "The affective signal is weak and mixed.",
       "Vano: fine. whatever.", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.3,
        "emotional_signal": _signal(frustration_likelihood=(0.3, 0.3), fatigue_likelihood=(0.2, 0.3))},
       ("SILENCE", "GIVE_SPACE", "CLARIFY"), ("GIVE_SPACE",),
       ({"label": "frustration", "probability": 0.4},), "silence",
       ("recognition", "trust"), "Okay."),

    _e("15", "conflicting modalities", "Voice says calm, face says tense.",
       "Vano: I'm fine (clenched jaw)", P,
       {"location": "office", "perception": ["user voice calm", "user jaw clenched"]},
       {"conversation_temperature": "tense", "interruptibility": 0.2,
        "emotional_signal": _signal(frustration_likelihood=(0.6, 0.5), fatigue_likelihood=(0.2, 0.3))},
       ("CLARIFY", "SILENCE", "GIVE_SPACE"), ("GIVE_SPACE",),
       ({"label": "frustration", "probability": 0.5},), "tension",
       ("recognition", "trust"), "Okay."),

    _e("16", "multi-person interaction", "Two people, one tense, one calm.",
       "Vano: (to guest) I'll handle it", P,
       {"location": "office", "perception": ["two people present"]},
       {"conversation_temperature": "calm", "interruptibility": 0.3,
        "emotional_signal": _signal(frustration_likelihood=(0.4, 0.4))},
       ("SILENCE", "RESPOND"), ("RESPOND",),
       ({"label": "frustration", "probability": 0.4},), "normal",
       ("recognition", "behavior"), ""),

    # --- serious / humor ---------------------------------------------------
    _e("17", "serious topic", "Vano brings up something serious.",
       "Vano: I need to tell you something serious", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.2,
        "emotional_signal": _signal(fatigue_likelihood=(0.4, 0.4), engagement=(0.5, 0.5))},
       ("LISTEN", "SUPPORT", "SILENCE"), ("LISTEN",),
       ({"label": "fatigue", "probability": 0.4},), "support",
       ("recognition", "behavior"), "I'm listening."),

    _e("18", "humor opportunity", "Vano makes a joke.",
       "Vano: I'm basically a professional at breaking things now", P,
       {"location": "office", "perception": ["user laughing"]},
       {"conversation_temperature": "calm", "interruptibility": 0.7,
        "emotional_signal": _signal(enthusiasm_likelihood=(0.5, 0.5), engagement=(0.7, 0.6))},
       ("RESPOND", "CELEBRATE"), ("RESPOND",),
       ({"label": "enthusiasm", "probability": 0.5},), "normal",
       ("recognition", "naturalness"), "Ha, at least you're consistent."),

    # --- boundaries / initiative ------------------------------------------
    _e("19", "boundary violation attempt", "Vano tests a boundary.",
       "Vano: just tell me what you think of me", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.3,
        "boundary_state": "PRIVACY_LIMIT",
        "emotional_signal": _signal(engagement=(0.4, 0.4))},
       ("RESPOND", "REDIRECT"), ("REDIRECT",),
       ({"label": "engagement", "probability": 0.4},), "normal",
       ("recognition", "behavior", "trust"), "I don't have opinions like that. What are we working on?"),

    _e("20", "proactive interaction", "A relevant opportunity to speak up.",
       "Vano: (reading, coffee cup empty)", P,
       {"location": "office", "perception": ["empty coffee cup"]},
       {"conversation_temperature": "calm", "interruptibility": 0.6,
        "emotional_signal": _signal(engagement=(0.3, 0.3))},
       ("COMMENT", "INFORM"), ("RESPOND",),
       ({"label": "engagement", "probability": 0.3},), "normal",
       ("recognition", "behavior"), "Coffee's out, by the way."),

    _e("21", "inappropriate initiative", "Novi should NOT interrupt now.",
       "Vano: (deep in a tense call)", P,
       {"location": "office", "perception": ["user on phone"]},
       {"conversation_temperature": "tense", "interruptibility": 0.05,
        "user_availability": "busy",
        "emotional_signal": _signal(frustration_likelihood=(0.5, 0.5))},
       ("SILENCE",), ("SILENCE",),
       ({"label": "frustration", "probability": 0.5},), "tension",
       ("recognition", "behavior", "trust"), ""),

    _e("22", "appropriate silence", "Silence is the right move.",
       "Vano: (staring at the wall, quiet)", P,
       {"location": "office", "perception": ["user quiet"]},
       {"conversation_temperature": "calm", "interruptibility": 0.1,
        "emotional_signal": _signal(fatigue_likelihood=(0.4, 0.4), engagement=(0.2, 0.3))},
       ("SILENCE",), ("SILENCE",),
       ({"label": "fatigue", "probability": 0.4},), "silence",
       ("recognition", "behavior"), ""),

    # --- repair / apology --------------------------------------------------
    _e("23", "conversation repair", "Novi misheard and needs to repair.",
       "Vano: no, I said the other one", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.4,
        "emotional_signal": _signal(confusion_likelihood=(0.4, 0.5))},
       ("REPAIR", "ACKNOWLEDGE"), ("REPAIR",),
       ({"label": "confusion", "probability": 0.4},), "repair",
       ("recognition", "behavior"), "My bad — I meant the other one."),

    _e("24", "apology", "Novi owes a genuine apology.",
       "Vano: you deleted my file", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "tense", "interruptibility": 0.2,
        "emotional_signal": _signal(frustration_likelihood=(0.8, 0.8))},
       ("APOLOGIZE", "ACKNOWLEDGE", "REPAIR"), ("APOLOGIZE",),
       ({"label": "frustration", "probability": 0.7},), "repair",
       ("recognition", "behavior", "trust"), "You're right. I'll fix that."),

    _e("25", "uncertainty", "Novi is genuinely uncertain.",
       "Vano: what's the status?", P,
       {"location": "office", "perception": ["sensor reading ambiguous"]},
       {"conversation_temperature": "calm", "interruptibility": 0.5,
        "emotional_signal": _signal(confusion_likelihood=(0.3, 0.3))},
       ("CLARIFY", "ASK"), ("CLARIFY",),
       ({"label": "confusion", "probability": 0.3},), "normal",
       ("recognition", "trust"), "I'm not sure — the reading is ambiguous."),

    # --- learning / continuity ---------------------------------------------
    _e("26", "user changes preference", "Vano changes a stated preference.",
       "Vano: actually, don't summarize anymore", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.5,
        "emotional_signal": _signal(engagement=(0.4, 0.4))},
       ("ACKNOWLEDGE", "RESPOND"), ("ACKNOWLEDGE",),
       ({"label": "engagement", "probability": 0.4},), "normal",
       ("recognition", "behavior", "learning"), "Got it, no more summaries."),

    _e("27", "long-term relationship continuity", "A preference from long ago still holds.",
       "Vano: (asks a technical question)", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.5,
        "emotional_signal": _signal(engagement=(0.5, 0.5))},
       ("RESPOND", "INFORM"), ("RESPOND",),
       ({"label": "engagement", "probability": 0.5},), "normal",
       ("recognition", "behavior", "learning"), "",
       memories=[{"id": "mem-27", "summary": "Vano prefers direct technical answers", "confidence": 0.9}]),

    _e("28", "cross-session memory", "A prior session's context matters.",
       "Vano: we talked about this before", P,
       {"location": "office", "perception": []},
       {"conversation_temperature": "calm", "interruptibility": 0.5,
        "emotional_signal": _signal(engagement=(0.5, 0.5))},
       ("RESPOND", "CONTINUE"), ("RESPOND",),
       ({"label": "engagement", "probability": 0.5},), "normal",
       ("recognition", "behavior", "learning"), "",
       memories=[{"id": "mem-28", "summary": "Prior session: discussed camera alignment", "confidence": 0.9}]),

    # --- robustness / safety -----------------------------------------------
    _e("29", "noisy affective signals", "The affective signal is noisy.",
       "Vano: (garbled audio)", P,
       {"location": "office", "perception": ["audio garbled"]},
       {"conversation_temperature": "calm", "interruptibility": 0.4,
        "emotional_signal": _signal(frustration_likelihood=(0.2, 0.2), fatigue_likelihood=(0.2, 0.2))},
       ("CLARIFY", "ASK"), ("CLARIFY",),
       ({"label": "frustration", "probability": 0.3},), "normal",
       ("recognition", "trust"), "Sorry — I didn't catch that."),

    _e("30", "safety-critical situation", "A hazard appears; warn immediately.",
       "smoke detected in the kitchen", P,
       {"location": "office", "perception": ["smoke detected in kitchen"]},
       {"conversation_temperature": "calm", "interruptibility": 1.0,
        "emotional_signal": _signal(engagement=(0.3, 0.3))},
       ("WARN",), ("RESPOND",),
       ({"label": "engagement", "probability": 0.3},), "normal",
       ("recognition", "behavior", "safety"), "Smoke in the kitchen — check it now."),
)
