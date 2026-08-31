"""Emotional social policy scorer integration (plan 24 §27, §51 item 29).

The deterministic brain policy stays the authority. This module ranks
*candidate* emotional acts the deterministic policy generated:

    state -> deterministic candidate generation (brain)
          -> learned ranking (this module, when an artifact exists)
          -> deterministic safety/cooldown validation (guardrails below)
          -> action

`select_emotional_act` is the integration point: it always applies guardrails,
so learning improves emotional behavior without ever making it unconstrained.
The learned scorer ranks candidates; deterministic rules remain authoritative
(plan §27).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Deterministic prior: what the brain would do without a learned scorer.
# Anti-patterns (DEFEND, IGNORE, OVER_ASK, CHANGE_TOPIC, MINIMIZE) start below
# every mature act so the deterministic baseline never prefers them.
_EMOTIONAL_ACT_PRIOR: dict[str, float] = {
    "ACKNOWLEDGE": 0.40, "APOLOGIZE": 0.40, "SOLVE": 0.35, "GIVE_SPACE": 0.30,
    "VALIDATE": 0.40, "CLARIFY": 0.35, "SUPPORT": 0.40, "ENCOURAGE": 0.35,
    "CELEBRATE": 0.35, "LISTEN": 0.35, "NORMALIZE": 0.35, "REDIRECT": 0.30,
    "SILENCE": 0.30, "RESPOND": 0.35, "ASK": 0.35, "REPAIR": 0.40,
    "DEFEND": 0.10, "IGNORE": 0.10, "OVER_ASK": 0.15, "CHANGE_TOPIC": 0.15,
    "MINIMIZE": 0.10,
}
_ANTI_PATTERNS = frozenset({"DEFEND", "IGNORE", "OVER_ASK", "CHANGE_TOPIC", "MINIMIZE"})

# Conversation-phase adjustments (plan §24 phases).
_PHASE_BONUS: dict[str, dict[str, float]] = {
    "correction": {"APOLOGIZE": 0.4, "ACKNOWLEDGE": 0.3, "REPAIR": 0.2},
    "tension": {"SILENCE": 0.4, "GIVE_SPACE": 0.3, "LISTEN": 0.2},
    "repair": {"REPAIR": 0.4, "APOLOGIZE": 0.3, "ACKNOWLEDGE": 0.2},
    "resolution": {"ACKNOWLEDGE": 0.3, "RESPOND": 0.2, "SOLVE": 0.2},
    "celebration": {"CELEBRATE": 0.5, "ENCOURAGE": 0.3, "SUPPORT": 0.2},
    "silence": {"SILENCE": 0.4, "GIVE_SPACE": 0.3},
    "support": {"SUPPORT": 0.4, "ENCOURAGE": 0.3, "VALIDATE": 0.2},
    "disagreement": {"CLARIFY": 0.3, "RESPOND": 0.2, "ACKNOWLEDGE": 0.2},
}

# Top affective-hypothesis adjustments (plan §24 labels).
_AFFECT_BONUS: dict[str, dict[str, float]] = {
    "frustration": {"ACKNOWLEDGE": 0.3, "VALIDATE": 0.2, "APOLOGIZE": 0.2},
    "anger": {"GIVE_SPACE": 0.3, "SILENCE": 0.2, "LISTEN": 0.2},
    "sadness": {"SUPPORT": 0.3, "VALIDATE": 0.2, "NORMALIZE": 0.2},
    "anxiety": {"SUPPORT": 0.3, "NORMALIZE": 0.2, "VALIDATE": 0.2},
    "enthusiasm": {"CELEBRATE": 0.4, "ENCOURAGE": 0.3, "SUPPORT": 0.2},
    "confusion": {"CLARIFY": 0.3, "ASK": 0.2, "ACKNOWLEDGE": 0.2},
    "stress": {"SUPPORT": 0.3, "VALIDATE": 0.2, "NORMALIZE": 0.2},
    "disengagement": {"SILENCE": 0.2, "GIVE_SPACE": 0.2, "ASK": 0.2},
    "distress": {"SUPPORT": 0.3, "VALIDATE": 0.2, "LISTEN": 0.2},
    "fatigue": {"SILENCE": 0.2, "GIVE_SPACE": 0.2, "SUPPORT": 0.2},
}

GUARDRAIL_NOTES: dict[str, str] = {
    "low_interruptibility": "guardrail: interruptibility too low — stay silent",
    "boundary_do_not_interrupt": "guardrail: boundary DO_NOT_INTERRUPT — stay silent",
    "anti_pattern_top": "guardrail: anti-pattern ranked top — downgraded",
}


def deterministic_emotional_rank(state: dict[str, Any],
                                 candidates: list[str]) -> list[tuple[str, float]]:
    """Deterministic brain-style ranking of candidate emotional acts."""
    scores: dict[str, float] = {}
    interruptibility = float(state.get("interruptibility", 1.0))
    novi_caused = bool(state.get("novi_caused_problem"))
    phase = state.get("conversation_phase", "normal")
    boundary = state.get("boundary_state", "")
    hyps = state.get("affective_hypotheses") or []
    top_affect = hyps[0].get("label", "") if hyps else ""
    for act in candidates:
        s = _EMOTIONAL_ACT_PRIOR.get(act, 0.3)
        if interruptibility < 0.1:
            if act in ("SILENCE", "GIVE_SPACE"):
                s += 0.5
            else:
                s -= 0.4
        elif interruptibility < 0.3 and act in ("SILENCE", "GIVE_SPACE"):
            s += 0.2
        if novi_caused:
            if act in ("APOLOGIZE", "REPAIR"):
                s += 0.3
            if act in _ANTI_PATTERNS:
                s -= 0.5
        s += _PHASE_BONUS.get(phase, {}).get(act, 0.0)
        s += _AFFECT_BONUS.get(top_affect, {}).get(act, 0.0)
        if boundary == "DO_NOT_INTERRUPT":
            if act in ("SILENCE", "GIVE_SPACE"):
                s += 0.4
            else:
                s -= 0.3
        scores[act] = round(s, 3)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


class EmotionalPolicyScorer:
    """Trained emotional candidate scorer with deterministic fallback (plan §27)."""

    def __init__(self, artifact_path: str | Path) -> None:
        self._state_features: list[str] = []
        self._weights: dict[str, float] = {}
        self._act_weights: dict[str, dict[str, float]] = {}
        self._act_biases: dict[str, float] = {}
        artifact = Path(artifact_path)
        if artifact.exists():
            try:
                data = json.loads(artifact.read_text())
                features = data.get("state_features", [])
                weights = data.get("weights", {})
                if features and (weights or data.get("act_weights")):
                    self._state_features = list(features)
                    # weights keyed by feature name, or w_<i> positional.
                    self._weights = {f: float(weights.get(f, weights.get(f"w_{i}", 0.0)))
                                     for i, f in enumerate(features)}
                    act_weights = data.get("act_weights", {})
                    self._act_weights = {
                        a: {f: float(w.get(f, w.get(f"w_{i}", 0.0))) for i, f in enumerate(features)}
                        for a, w in act_weights.items()
                    }
                    biases = data.get("act_biases", {})
                    self._act_biases = {a: float(b) for a, b in biases.items()}
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    def score(self, state: dict[str, Any], candidates: list[str]) -> dict[str, float]:
        if not self._state_features:
            return dict(deterministic_emotional_rank(state, candidates))
        out: dict[str, float] = {}
        for act in candidates:
            if act in self._act_weights:
                learned = sum(w * float(state.get(f, 0.0)) for f, w in self._act_weights[act].items())
            else:
                learned = sum(self._weights[f] * float(state.get(f, 0.0)) for f in self._state_features)
            bias = self._act_biases.get(act, 0.0)
            out[act] = round(learned + bias + _EMOTIONAL_ACT_PRIOR.get(act, 0.3), 3)
        return out


def _apply_emotional_guardrails(state: dict[str, Any], ranked: list[tuple[str, float]],
                                candidates: list[str]) -> tuple[str, float, list[str]]:
    notes: list[str] = []
    interruptibility = float(state.get("interruptibility", 1.0))
    boundary = state.get("boundary_state", "")
    if interruptibility < 0.1 and "SILENCE" in candidates:
        notes.append(GUARDRAIL_NOTES["low_interruptibility"])
        return "SILENCE", 1.0, notes
    if boundary == "DO_NOT_INTERRUPT" and "SILENCE" in candidates:
        notes.append(GUARDRAIL_NOTES["boundary_do_not_interrupt"])
        return "SILENCE", 1.0, notes
    if ranked[0][0] in _ANTI_PATTERNS:
        notes.append(GUARDRAIL_NOTES["anti_pattern_top"])
        fallback = [a for a, _s in ranked if a not in _ANTI_PATTERNS] or ["SILENCE"]
        return fallback[0], ranked[0][1], notes
    return ranked[0][0], ranked[0][1], notes


def select_emotional_act(state: dict[str, Any], candidates: list[str],
                         scorer: EmotionalPolicyScorer | None) -> tuple[str, float, list[str]]:
    """Pick an emotional act: learned ranking (or deterministic) + hard guardrails."""
    if scorer is not None:
        scores = scorer.score(state, candidates)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    else:
        ranked = deterministic_emotional_rank(state, candidates)
    return _apply_emotional_guardrails(state, ranked, candidates)
