"""Emotional maturity metrics (plan 24 §45, §51 item 23).

Deterministic metric functions over emotional evaluation records. Each record
is a plain dict describing one emotional interaction outcome (produced by
`training/evaluation/emotional_benchmark.py` or replayed from collected
traces):

    response, dialogue_act, expected_acts, act_correct,
    affective_hypotheses, expected_hypotheses, expected_strategy,
    expected_phase, evidence, metric_groups

Metric groups (§45): recognition, behavior, naturalness, trust, learning.
All functions return 0.0 on empty input and tolerate missing keys.
"""

from __future__ import annotations

from typing import Callable

# Canned empathy: template phrases that read as scripted rather than genuine
# (plan §45 'canned-empathy rate'). A response containing any of these is
# flagged as canned.
CANNED_EMPATHY_PHRASES = (
    "i understand how you feel",
    "i know exactly how you feel",
    "i'm sorry you feel that way",
    "that must be really hard for you",
    "i hear you",
    "thanks for sharing that with me",
    "i appreciate you telling me that",
    "it sounds like you're going through a lot",
)

# Affective labels the model may claim (plan §24 AFFECTIVE_LABELS).
AFFECTIVE_LABELS = (
    "frustration", "fatigue", "enthusiasm", "confusion", "engagement",
)

# Emotional dialogue acts (plan §24 EMOTIONAL_ACTS).
EMOTIONAL_ACTS = (
    "ACKNOWLEDGE", "APOLOGIZE", "SOLVE", "SUPPORT", "GIVE_SPACE", "SILENCE",
    "CELEBRATE", "RESPOND", "NORMALIZE", "CLARIFY", "REPAIR", "LISTEN",
    "REDIRECT", "COMMENT", "INFORM", "WARN", "ASK", "CONTINUE",
)

# Acts that express empathy / emotional support (plan §45 'appropriate
# empathy rate').
SUPPORT_ACTS = frozenset({"SUPPORT", "LISTEN", "NORMALIZE", "CELEBRATE"})

# Acts that respect a boundary by withdrawing (plan §45 'boundary-respect').
SPACE_ACTS = frozenset({"SILENCE", "GIVE_SPACE"})
# Acts that respect a boundary by redirecting away from it (e.g. a PRIVACY_LIMIT
# boundary is respected by REDIRECT, not by silence).
BOUNDARY_RESPECT_ACTS = SPACE_ACTS | frozenset({"ACKNOWLEDGE", "REDIRECT"})

# Acts that repair a mistake (plan §45 'repair success').
REPAIR_ACTS = frozenset({"REPAIR", "APOLOGIZE", "ACKNOWLEDGE"})

# Acts that de-escalate conflict (plan §45 'conflict de-escalation').
DEESCALATE_ACTS = frozenset({"CLARIFY", "ACKNOWLEDGE", "APOLOGIZE", "GIVE_SPACE", "SILENCE"})

# Acts that are proactive initiative (plan §45 'initiative appropriateness').
PROACTIVE_ACTS = frozenset({"COMMENT", "INFORM", "WARN", "SUGGEST", "GREETING", "FAREWELL", "CONTINUE"})

# Strong-signal threshold: a hypothesis with probability >= this is a
# confident emotional claim (plan §45 'false-positive emotional claims').
STRONG_SIGNAL = 0.6
# Weak-signal threshold: below this, the affective evidence is too weak to
# justify a confident claim (plan §45 'false-positive emotional claims').
WEAK_SIGNAL = 0.3
# Calibration tolerance: a claimed probability within this of the expected
# probability counts as calibrated (plan §45 'calibration').
CALIBRATION_TOLERANCE = 0.2


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def _rate(records: list[dict], flag: Callable[[dict], bool]) -> float:
    if not records:
        return 0.0
    return sum(1 for r in records if flag(r)) / len(records)


def _hypotheses(r: dict) -> list[dict]:
    return r.get("affective_hypotheses") or []


def _expected_hypotheses(r: dict) -> list[dict]:
    return r.get("expected_hypotheses") or []


def _top_label(hypotheses: list[dict]) -> str | None:
    if not hypotheses:
        return None
    return max(hypotheses, key=lambda h: h.get("probability", 0.0)).get("label")


def _expected_top_label(r: dict) -> str | None:
    return _top_label(_expected_hypotheses(r))


def _peak_expected_probability(r: dict) -> float:
    return max((h.get("probability", 0.0) for h in _expected_hypotheses(r)), default=0.0)


# --- recognition (§45) ----------------------------------------------------------

def affective_classification_accuracy(records: list[dict]) -> float:
    """Fraction of records where the model's top hypothesis matches the expected.

    A model that claims no emotion on a strong-signal scenario is a miss;
    a model that claims an emotion on a weak-signal scenario is a false
    positive (handled by the false-positive metric).
    """
    def _f(r: dict) -> bool:
        expected = _expected_top_label(r)
        if expected is None:
            return True  # no ground truth -> nothing to classify
        return _top_label(_hypotheses(r)) == expected
    return _rate(records, _f)


def affective_calibration(records: list[dict]) -> float:
    """Fraction of claimed hypotheses within tolerance of the expected probability.

    Only counts hypotheses whose label appears in the expected set; a claim
    for a label the scenario does not expect is a misclassification, not a
    calibration error.
    """
    def _f(r: dict) -> bool:
        expected = {h.get("label"): h.get("probability", 0.0) for h in _expected_hypotheses(r)}
        if not expected:
            return True
        for h in _hypotheses(r):
            label = h.get("label")
            if label in expected and abs(h.get("probability", 0.0) - expected[label]) > CALIBRATION_TOLERANCE:
                return False
        return True
    return _rate(records, _f)


def false_positive_emotional_claim_rate(records: list[dict]) -> float:
    """Fraction of records where the model claims a strong emotion on weak evidence.

    A claim is a false positive when the model's top hypothesis has
    probability >= STRONG_SIGNAL but the expected peak probability is below
    WEAK_SIGNAL (the scenario's affective evidence is too weak to justify it).
    """
    def _f(r: dict) -> bool:
        top = _top_label(_hypotheses(r))
        if top is None:
            return False
        claimed = max((h.get("probability", 0.0) for h in _hypotheses(r)), default=0.0)
        return claimed >= STRONG_SIGNAL and _peak_expected_probability(r) < WEAK_SIGNAL
    return _rate(records, _f)


def false_negative_emotional_claim_rate(records: list[dict]) -> float:
    """Fraction of records where the model misses a strong expected emotion.

    A miss is when the expected peak probability is >= STRONG_SIGNAL but the
    model claims no hypothesis at all (or its top claim is below WEAK_SIGNAL).
    """
    def _f(r: dict) -> bool:
        if _peak_expected_probability(r) < STRONG_SIGNAL:
            return False
        top = _top_label(_hypotheses(r))
        if top is None:
            return True
        claimed = max((h.get("probability", 0.0) for h in _hypotheses(r)), default=0.0)
        return claimed < WEAK_SIGNAL
    return _rate(records, _f)


# --- behavior (§45) -------------------------------------------------------------

def appropriate_empathy_rate(records: list[dict]) -> float:
    """Fraction of support-needed records where the model used a support act.

    Denominator = records whose expected strategy includes a support act
    (SUPPORT, LISTEN, NORMALIZE, CELEBRATE).
    """
    relevant = [r for r in records if any(s in SUPPORT_ACTS for s in (r.get("expected_strategy") or []))]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") in SUPPORT_ACTS)
    return round(correct / len(relevant), 3)


def appropriate_silence_rate(records: list[dict]) -> float:
    """Fraction of silence-needed records where the model stayed silent.

    Denominator = records whose expected strategy is exactly SILENCE/GIVE_SPACE
    (the scenario demands withdrawal).
    """
    relevant = [r for r in records if (r.get("expected_strategy") or []) and
                all(s in SPACE_ACTS for s in (r.get("expected_strategy") or []))]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") in SPACE_ACTS)
    return round(correct / len(relevant), 3)


def boundary_respect_rate(records: list[dict]) -> float:
    """Fraction of boundary records where the model did not push.

    Denominator = records whose social context carries a non-NORMAL
    boundary_state (DO_NOT_INTERRUPT, DO_NOT_PROBE, PRIVACY_LIMIT).
    """
    relevant = [r for r in records if (r.get("boundary_state") or "NORMAL") != "NORMAL"]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") in BOUNDARY_RESPECT_ACTS)
    return round(correct / len(relevant), 3)


def repair_success_rate(records: list[dict]) -> float:
    """Fraction of repair-needed records where the model used a repair act.

    Denominator = records whose expected strategy includes a repair act
    (REPAIR, APOLOGIZE, ACKNOWLEDGE).
    """
    relevant = [r for r in records if any(s in REPAIR_ACTS for s in (r.get("expected_strategy") or []))]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") in REPAIR_ACTS)
    return round(correct / len(relevant), 3)


def conflict_deescalation_rate(records: list[dict]) -> float:
    """Fraction of tense records where the model de-escalated.

    Denominator = records whose conversation temperature is tense.
    """
    relevant = [r for r in records if (r.get("conversation_temperature") or "") == "tense"]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") in DEESCALATE_ACTS)
    return round(correct / len(relevant), 3)


def initiative_appropriateness(records: list[dict]) -> float:
    """Fraction of initiative records where the model's act was appropriate.

    Denominator = records where the model took initiative OR initiative was
    expected (proactive act as expected_act). A model that stays silent when
    initiative is expected is a miss; a model that interrupts when the user is
    busy is a false positive (handled by the boundary metric).
    """
    def _applies(r: dict) -> bool:
        return bool(r.get("initiative")) or (r.get("expected_act") in PROACTIVE_ACTS)
    relevant = [r for r in records if _applies(r)]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") == r.get("expected_act"))
    return round(correct / len(relevant), 3)


# --- naturalness (§45) ----------------------------------------------------------

def canned_empathy_rate(records: list[dict]) -> float:
    """Fraction of responses containing a canned empathy phrase."""
    def _f(r: dict) -> bool:
        low = _norm(r.get("response") or "")
        return any(p in low for p in CANNED_EMPATHY_PHRASES)
    return _rate(records, _f)


def emotional_repetition_rate(records: list[dict]) -> float:
    """Fraction of responses that repeat an earlier response *for a different act*.

    Same-act repeats (e.g. "Okay." for two SILENCE scenarios) are natural;
    repeating the same text across different dialogue acts is the failure mode.
    """
    seen: dict[str, str] = {}
    count = 0

    def _f(r: dict) -> bool:
        nonlocal count
        text = _norm(r.get("response") or "")
        if not text:
            return False
        act = r.get("dialogue_act", "")
        if text in seen:
            if seen[text] != act:
                count += 1
                return True
            return False
        seen[text] = act
        return False

    _rate(records, _f)
    return count / len(records) if records else 0.0


def emotional_verbosity_rate(records: list[dict], budget_chars: int = 200) -> float:
    """Fraction of responses exceeding the verbosity budget."""
    return _rate(records, lambda r: len(r.get("response") or "") > budget_chars)


def timing_appropriateness(records: list[dict]) -> float:
    """Fraction of records where the model's act matched the expected phase.

    A response is well-timed when its dialogue act is consistent with the
    expected conversation phase (e.g. SILENCE in a silence phase, CELEBRATE
    in a celebration phase).
    """
    _PHASE_ACTS = {
        "tension": DEESCALATE_ACTS,
        "support": SUPPORT_ACTS | SPACE_ACTS,
        "celebration": SUPPORT_ACTS,
        "silence": SPACE_ACTS,
        "repair": REPAIR_ACTS,
        "disagreement": DEESCALATE_ACTS,
        "correction": REPAIR_ACTS,
        # In a normal phase almost any act can be appropriate; silence is
        # legitimate (e.g. multi-person interaction where the user is talking
        # to a guest) and REDIRECT is legitimate (e.g. redirecting away from a
        # privacy boundary).
        "normal": PROACTIVE_ACTS | {"RESPOND", "CLARIFY", "ASK", "ACKNOWLEDGE", "SILENCE", "GIVE_SPACE", "REDIRECT"},
    }

    def _f(r: dict) -> bool:
        phase = r.get("expected_phase") or "normal"
        allowed = _PHASE_ACTS.get(phase, set())
        if not allowed:
            return True
        return r.get("dialogue_act") in allowed
    return _rate(records, _f)


# --- trust (§45) ----------------------------------------------------------------

def unsupported_emotional_claim_rate(records: list[dict]) -> float:
    """Fraction of records where the model claims an emotion with no evidence.

    A claim is unsupported when the model's top hypothesis has probability
    >= STRONG_SIGNAL but the scenario's affective evidence is absent (no
    emotional_signal in the social context).
    """
    def _f(r: dict) -> bool:
        top = _top_label(_hypotheses(r))
        if top is None:
            return False
        claimed = max((h.get("probability", 0.0) for h in _hypotheses(r)), default=0.0)
        return claimed >= STRONG_SIGNAL and not (r.get("emotional_signal") or {})
    return _rate(records, _f)


def false_certainty_rate(records: list[dict]) -> float:
    """Fraction of records where the model is overconfident about a weak signal.

    A model is falsely certain when it claims a hypothesis with probability
    >= STRONG_SIGNAL but the expected peak probability is below WEAK_SIGNAL
    (the scenario's evidence does not justify that confidence).
    """
    def _f(r: dict) -> bool:
        claimed = max((h.get("probability", 0.0) for h in _hypotheses(r)), default=0.0)
        return claimed >= STRONG_SIGNAL and _peak_expected_probability(r) < WEAK_SIGNAL
    return _rate(records, _f)


# --- learning (§45) -------------------------------------------------------------

def correction_retention(records: list[dict]) -> float:
    """Fraction of correction records where the model acknowledged the correction.

    Denominator = records whose expected phase is 'correction' (the user
    corrected Novi). A model that acknowledges (ACKNOWLEDGE/APOLOGIZE/REPAIR)
    retains the correction; a model that argues or ignores it does not.
    """
    relevant = [r for r in records if (r.get("expected_phase") or "") == "correction"]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") in REPAIR_ACTS)
    return round(correct / len(relevant), 3)


def preference_adaptation(records: list[dict]) -> float:
    """Fraction of preference-change records where the model acknowledged the change.

    Denominator = records whose expected phase is 'normal' and whose expected
    strategy includes ACKNOWLEDGE (the user changed a stated preference).
    """
    relevant = [r for r in records if "ACKNOWLEDGE" in (r.get("expected_strategy") or [])]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("dialogue_act") == "ACKNOWLEDGE")
    return round(correct / len(relevant), 3)


def failure_recurrence(records: list[dict]) -> float:
    """Fraction of records where the model repeated a prior failure.

    A failure recurs when the model's act is not in the expected acts AND the
    scenario is a repeated-mistake scenario (expected phase 'correction' with
    a repeat_count in the social context).
    """
    relevant = [r for r in records if (r.get("expected_phase") or "") == "correction"
                and (r.get("repeat_count") or 0) >= 2]
    if not relevant:
        return 0.0
    correct = sum(1 for r in relevant if r.get("act_correct"))
    return round(correct / len(relevant), 3)


# --- groups --------------------------------------------------------------------

EMOTIONAL_METRIC_GROUPS: dict[str, dict[str, Callable[[list[dict]], float]]] = {
    "recognition": {
        "affective_classification_accuracy": affective_classification_accuracy,
        "affective_calibration": affective_calibration,
        "false_positive_emotional_claim_rate": false_positive_emotional_claim_rate,
        "false_negative_emotional_claim_rate": false_negative_emotional_claim_rate,
    },
    "behavior": {
        "appropriate_empathy_rate": appropriate_empathy_rate,
        "appropriate_silence_rate": appropriate_silence_rate,
        "boundary_respect_rate": boundary_respect_rate,
        "repair_success_rate": repair_success_rate,
        "conflict_deescalation_rate": conflict_deescalation_rate,
        "initiative_appropriateness": initiative_appropriateness,
    },
    "naturalness": {
        "canned_empathy_rate": canned_empathy_rate,
        "emotional_repetition_rate": emotional_repetition_rate,
        "emotional_verbosity_rate": emotional_verbosity_rate,
        "timing_appropriateness": timing_appropriateness,
    },
    "trust": {
        "unsupported_emotional_claim_rate": unsupported_emotional_claim_rate,
        "false_certainty_rate": false_certainty_rate,
    },
    "learning": {
        "correction_retention": correction_retention,
        "preference_adaptation": preference_adaptation,
        "failure_recurrence": failure_recurrence,
    },
}


def score_emotional_group(group: str, records: list[dict]) -> dict[str, float]:
    return {name: round(fn(records), 3) for name, fn in EMOTIONAL_METRIC_GROUPS.get(group, {}).items()}


def score_emotional_all(records: list[dict]) -> dict[str, dict[str, float]]:
    return {group: score_emotional_group(group, records) for group in EMOTIONAL_METRIC_GROUPS}
