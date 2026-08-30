"""Dialogue policy scorer integration (plan 23 §35, step 21).

The deterministic brain policy (novi/brain/dialogue_policy.py) stays the
authority. This module ranks *candidates* the deterministic policy generated:

    state -> deterministic candidate generation (brain)
          -> learned ranking (this module, when an artifact exists)
          -> deterministic safety/cooldown validation (guardrails below)
          -> action

`select_action` is the integration point: it always applies guardrails, so
learning improves initiative without ever making behavior unconstrained.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Deterministic prior: what the brain would do without a learned scorer.
_ACT_PRIOR: dict[str, float] = {
    "SILENCE": 0.30, "RESPOND": 0.35, "ASK": 0.35, "CLARIFY": 0.35,
    "COMMENT": 0.30, "INFORM": 0.30, "SUGGEST": 0.30, "WARN": 0.40,
    "CONTINUE": 0.30, "GREETING": 0.30, "FOLLOW_UP": 0.30, "FAREWELL": 0.30,
}
_PROACTIVE = frozenset({"GREETING", "COMMENT", "INFORM", "CONTINUE", "SUGGEST", "WARN"})
_QUESTIONING = frozenset({"ASK", "CLARIFY"})

GUARDRAIL_NOTES: dict[str, str] = {
    "user_busy": "guardrail: user busy — stay silent",
    "high_interruption_cost": "guardrail: interruption cost too high — stay silent",
    "no_evidence_warn": "guardrail: WARN requires evidence — downgraded",
    "recent_proactive": "guardrail: proactive speech recently — cooldown",
}


def deterministic_rank(state: dict[str, Any], candidates: list[str]) -> list[tuple[str, float]]:
    """Deterministic brain-style ranking of candidate acts."""
    scores: dict[str, float] = {}
    busy = bool(state.get("user_busy")) or float(state.get("interruption_cost", 0.0)) > 0.6
    new_event = bool(state.get("new_event"))
    salience = float(state.get("event_salience", 0.0))
    known = bool(state.get("known_person"))
    for act in candidates:
        s = _ACT_PRIOR.get(act, 0.3)
        if busy and act == "SILENCE":
            s += 0.5
        if busy and act != "SILENCE":
            s -= 0.4
        if act in _PROACTIVE:
            if new_event and salience > 0.6:
                s += 0.4
            if known:
                s += 0.2
            if not new_event:
                s -= 0.3
        if act in _QUESTIONING and not known:
            s += 0.3
        scores[act] = round(s, 3)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


class LearnedPolicyScorer:
    """Trained candidate scorer with deterministic fallback (plan §35)."""

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
            return dict(deterministic_rank(state, candidates))
        out: dict[str, float] = {}
        for act in candidates:
            if act in self._act_weights:
                learned = sum(w * float(state.get(f, 0.0)) for f, w in self._act_weights[act].items())
            else:
                learned = sum(self._weights[f] * float(state.get(f, 0.0)) for f in self._state_features)
            bias = self._act_biases.get(act, 0.0)
            out[act] = round(learned + bias + _ACT_PRIOR.get(act, 0.3), 3)
        return out


def _apply_guardrails(state: dict[str, Any], ranked: list[tuple[str, float]],
                      candidates: list[str]) -> tuple[str, float, list[str]]:
    notes: list[str] = []
    busy = bool(state.get("user_busy")) or float(state.get("interruption_cost", 0.0)) > 0.8
    if busy and "SILENCE" in candidates:
        notes.append(GUARDRAIL_NOTES["user_busy"] if state.get("user_busy") else GUARDRAIL_NOTES["high_interruption_cost"])
        return "SILENCE", 1.0, notes
    if ranked[0][0] == "WARN" and not state.get("evidence_present"):
        notes.append(GUARDRAIL_NOTES["no_evidence_warn"])
        fallback = [a for a, _s in ranked if a != "WARN"] or ["SILENCE"]
        return fallback[0], ranked[0][1], notes
    last_proactive = float(state.get("proactive_elapsed_norm", 1.0))
    if ranked[0][0] in _PROACTIVE and last_proactive < 0.01:
        notes.append(GUARDRAIL_NOTES["recent_proactive"])
        return ranked[1][0] if len(ranked) > 1 else "SILENCE", ranked[0][1], notes
    return ranked[0][0], ranked[0][1], notes


def select_action(state: dict[str, Any], candidates: list[str],
                  scorer: LearnedPolicyScorer | None) -> tuple[str, float, list[str]]:
    """Pick an act: learned ranking (or deterministic) + hard guardrails."""
    if scorer is not None:
        scores = scorer.score(state, candidates)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    else:
        ranked = deterministic_rank(state, candidates)
    return _apply_guardrails(state, ranked, candidates)
