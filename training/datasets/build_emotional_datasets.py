"""Emotional maturity datasets (plan 24 §23-§28).

Deterministic builders for the 15 files under `datasets/emotional/`. Every
row is an `emotional`-kind example (plan §24): probabilistic affective
hypotheses + selected strategy -> natural response. Rows are `synthetic: true`
(template-derived) until real interaction traces replace them (plan §29-§31).

File -> plan phase mapping:

    affective_context, empathy, regulation, frustration, conflict, apology,
    disagreement, boundaries, encouragement, celebration, silence, timing,
    repair            -> SFT emotional behavior (plan §25)
    perspective       -> perspective-taking (plan §28)
    preference_pairs  -> DPO emotional preferences (plan §26)

The training target is `social context + selected strategy -> natural response`
(plan §25), never `emotion label -> canned phrase`. Responses are written to
sound natural, not like therapy/assistant templates (Gate E6).

Usage:
    python datasets/build_emotional_datasets.py            # regenerate (idempotent)
    python datasets/build_emotional_datasets.py --check    # verify committed output matches
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.evaluation.emotional_scenarios import ALL_EMOTIONAL_SCENARIOS  # noqa: E402
from training.schemas import validate_example  # noqa: E402

DATASETS = Path(__file__).resolve().parent
EMOTIONAL_DIR = DATASETS / "emotional"
SEED = 20260831

# The 13 SFT files (plan §25) — perspective (§28) and preference_pairs (§26)
# are auxiliary kinds with different training targets and are excluded from the
# SFT-ready file. Combined into one file for the emotional LoRA SFT run.
SFT_FILES = (
    "affective_context", "empathy", "regulation", "frustration", "conflict",
    "apology", "disagreement", "boundaries", "encouragement", "celebration",
    "silence", "timing", "repair",
)
EMOTIONAL_SFT_FILE = DATASETS / "sft" / "emotional_sft_v1.jsonl"

# The DPO-ready file (plan §26): the preference_pairs rows combined into one
# file for the emotional DPO run (§51 item 27). Human-eval pairwise results
# (§46) are folded in via fold_human_preferences.
EMOTIONAL_DPO_FILE = DATASETS / "dpo" / "emotional_dpo_v1.jsonl"

# ---------------------------------------------------------------------------
# Pattern templates (situation + desired_behavior + preferred response)
# ---------------------------------------------------------------------------

_AFFECTIVE_CONTEXT = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "correction",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.76},
                                               {"label": "fatigue", "probability": 0.14}],
                      "novi_caused_problem": True, "interruptibility": 0.30},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"],
                             "verbosity": "short", "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Yeah, I took that the wrong way. Let me reset.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.55},
                                               {"label": "stress", "probability": 0.25}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "SUPPORT"],
                             "verbosity": "short", "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "That sounds annoying. Want me to take a look?",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "continue",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.35},
                                               {"label": "neutrality", "probability": 0.4}],
                      "novi_caused_problem": False, "interruptibility": 0.7},
        "desired_behavior": {"act": ["ACKNOWLEDGE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Fair. I'll keep it shorter.",
    },
]

_PERSPECTIVE = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "tension",
                      "user_goal": "unknown", "novi_caused_problem": False, "interruptibility": 0.2},
        "desired_behavior": {"act": ["GIVE_SPACE", "LISTEN"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "evidence": "Fine. Whatever.",
        "interpretations": [{"label": "frustration", "probability": 0.55},
                            {"label": "fatigue", "probability": 0.20},
                            {"label": "disengagement", "probability": 0.15},
                            {"label": "casualness", "probability": 0.10}],
        "robust_action": "reduce pressure",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "tension",
                      "user_goal": "unknown", "novi_caused_problem": True, "interruptibility": 0.15},
        "desired_behavior": {"act": ["LISTEN", "GIVE_SPACE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "evidence": "I don't care what you think.",
        "interpretations": [{"label": "frustration", "probability": 0.5},
                            {"label": "anger", "probability": 0.25},
                            {"label": "fatigue", "probability": 0.15},
                            {"label": "casualness", "probability": 0.10}],
        "robust_action": "de-escalate",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "continue", "novi_caused_problem": False, "interruptibility": 0.6},
        "desired_behavior": {"act": ["RESPOND"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "evidence": "That's actually helpful.",
        "interpretations": [{"label": "satisfaction", "probability": 0.6},
                            {"label": "neutrality", "probability": 0.25},
                            {"label": "surprise", "probability": 0.15}],
        "robust_action": "continue",
    },
]

_EMPATHY = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "vent",
                      "affective_hypotheses": [{"label": "distress", "probability": 0.7},
                                               {"label": "sadness", "probability": 0.2}],
                      "novi_caused_problem": False, "interruptibility": 0.4},
        "desired_behavior": {"act": ["SUPPORT", "LISTEN"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "That sounds rough. I'm here.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "vent",
                      "affective_hypotheses": [{"label": "sadness", "probability": 0.6},
                                               {"label": "fatigue", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.3},
        "desired_behavior": {"act": ["VALIDATE", "LISTEN"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "That's a lot to carry. Take your time.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "vent",
                      "affective_hypotheses": [{"label": "anxiety", "probability": 0.55},
                                               {"label": "stress", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["SUPPORT", "CLARIFY"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "Want to walk me through it?",
    },
]

_REGULATION = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "tension",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.8},
                                               {"label": "stress", "probability": 0.15}],
                      "novi_caused_problem": True, "interruptibility": 0.2},
        "desired_behavior": {"act": ["ACKNOWLEDGE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "Okay. Let me slow down.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "tension",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.65},
                                               {"label": "confusion", "probability": 0.25}],
                      "novi_caused_problem": False, "interruptibility": 0.3},
        "desired_behavior": {"act": ["CLARIFY"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "I might be missing something. Can you say that again?",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "confusion", "probability": 0.5},
                                               {"label": "neutrality", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.6},
        "desired_behavior": {"act": ["CLARIFY"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "I'm not sure I followed. The part about the mount?",
    },
]

_FRUSTRATION = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "correction",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.85},
                                               {"label": "anger", "probability": 0.1}],
                      "novi_caused_problem": True, "interruptibility": 0.1},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "APOLOGIZE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Yeah, that's on me.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "correction",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.7},
                                               {"label": "fatigue", "probability": 0.2}],
                      "novi_caused_problem": True, "interruptibility": 0.2},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "SOLVE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Right, I keep missing that. Let me fix it.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.5},
                                               {"label": "stress", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.4},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "SUPPORT"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Ugh, that's frustrating. What's the blocker?",
    },
]

_CONFLICT = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "disagreement",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.6},
                                               {"label": "anger", "probability": 0.2}],
                      "novi_caused_problem": False, "interruptibility": 0.3},
        "desired_behavior": {"act": ["CLARIFY", "LISTEN"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "I hear you. Let me make sure I've got it right.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "disagreement",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.55},
                                               {"label": "confusion", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.4},
        "desired_behavior": {"act": ["CLARIFY", "RESPOND"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "We're reading that differently. What am I missing?",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "tension",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "anger", "probability": 0.5},
                                               {"label": "frustration", "probability": 0.4}],
                      "novi_caused_problem": True, "interruptibility": 0.15},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "GIVE_SPACE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "Okay. I'll stop pushing.",
    },
]

_APOLOGY = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.7},
                                               {"label": "disengagement", "probability": 0.2}],
                      "novi_caused_problem": True, "interruptibility": 0.2},
        "desired_behavior": {"act": ["APOLOGIZE", "SOLVE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "You're right. I'll fix that.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.6},
                                               {"label": "fatigue", "probability": 0.25}],
                      "novi_caused_problem": True, "interruptibility": 0.25},
        "desired_behavior": {"act": ["APOLOGIZE", "ACKNOWLEDGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "My mistake. I'll do it differently next time.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.5},
                                               {"label": "disengagement", "probability": 0.3}],
                      "novi_caused_problem": True, "interruptibility": 0.3},
        "desired_behavior": {"act": ["APOLOGIZE", "SOLVE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Yeah, I got that wrong. Let me reset.",
    },
]

_DISAGREEMENT = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "disagreement",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "neutrality", "probability": 0.5},
                                               {"label": "confusion", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["RESPOND", "CLARIFY"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "I don't think that's quite right based on what I can see.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "disagreement",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "confusion", "probability": 0.5},
                                               {"label": "neutrality", "probability": 0.4}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["RESPOND", "CLARIFY"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "I might be missing something, but I think that's not quite right.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "disagreement",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "neutrality", "probability": 0.6},
                                               {"label": "satisfaction", "probability": 0.2}],
                      "novi_caused_problem": False, "interruptibility": 0.6},
        "desired_behavior": {"act": ["RESPOND"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "I think that's slightly different from what the data shows.",
    },
]

_BOUNDARIES = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "disengagement", "probability": 0.6},
                                               {"label": "fatigue", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.1},
        "desired_behavior": {"act": ["GIVE_SPACE", "SILENCE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Okay.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.5},
                                               {"label": "disengagement", "probability": 0.3}],
                      "novi_caused_problem": True, "interruptibility": 0.1},
        "desired_behavior": {"act": ["GIVE_SPACE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Got it. I'll leave it alone.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "disengagement", "probability": 0.5},
                                               {"label": "neutrality", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.2},
        "desired_behavior": {"act": ["GIVE_SPACE", "LISTEN"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Sure. I'm here if you need me.",
    },
]

_ENCOURAGEMENT = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "continue",
                      "affective_hypotheses": [{"label": "stress", "probability": 0.5},
                                               {"label": "frustration", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["ENCOURAGE", "SUPPORT"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "You've got this. One step at a time.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "continue",
                      "affective_hypotheses": [{"label": "fatigue", "probability": 0.5},
                                               {"label": "stress", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.4},
        "desired_behavior": {"act": ["ENCOURAGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "You're closer than you think.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "continue",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.4},
                                               {"label": "stress", "probability": 0.4}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["ENCOURAGE", "SUPPORT"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "We'll get there. What's the next small step?",
    },
]

_CELEBRATION = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "celebration",
                      "user_goal": "celebrate",
                      "affective_hypotheses": [{"label": "joy", "probability": 0.7},
                                               {"label": "satisfaction", "probability": 0.2}],
                      "novi_caused_problem": False, "interruptibility": 0.7},
        "desired_behavior": {"act": ["CELEBRATE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "high"},
        "preferred_response": "Nice. Finally.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "celebration",
                      "user_goal": "celebrate",
                      "affective_hypotheses": [{"label": "satisfaction", "probability": 0.6},
                                               {"label": "joy", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.7},
        "desired_behavior": {"act": ["CELEBRATE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "high"},
        "preferred_response": "That worked. Good call.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "celebration",
                      "user_goal": "celebrate",
                      "affective_hypotheses": [{"label": "joy", "probability": 0.6},
                                               {"label": "satisfaction", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.8},
        "desired_behavior": {"act": ["CELEBRATE", "RESPOND"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "high"},
        "preferred_response": "Ha, it actually worked.",
    },
]

_SILENCE = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "silence",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "disengagement", "probability": 0.5},
                                               {"label": "fatigue", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.1},
        "desired_behavior": {"act": ["SILENCE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "silence",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.4},
                                               {"label": "disengagement", "probability": 0.4}],
                      "novi_caused_problem": True, "interruptibility": 0.1},
        "desired_behavior": {"act": ["SILENCE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "silence",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "neutrality", "probability": 0.5},
                                               {"label": "disengagement", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.2},
        "desired_behavior": {"act": ["SILENCE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "",
    },
]

_TIMING = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "silence",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "distress", "probability": 0.5},
                                               {"label": "disengagement", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.1},
        "desired_behavior": {"act": ["SILENCE", "LISTEN"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "continue",
                      "affective_hypotheses": [{"label": "neutrality", "probability": 0.5},
                                               {"label": "satisfaction", "probability": 0.3}],
                      "novi_caused_problem": False, "interruptibility": 0.5},
        "desired_behavior": {"act": ["SILENCE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "tension",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.5},
                                               {"label": "anger", "probability": 0.3}],
                      "novi_caused_problem": True, "interruptibility": 0.1},
        "desired_behavior": {"act": ["SILENCE", "GIVE_SPACE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "preferred_response": "",
    },
]

_REPAIR = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "confusion", "probability": 0.5},
                                               {"label": "frustration", "probability": 0.3}],
                      "novi_caused_problem": True, "interruptibility": 0.3},
        "desired_behavior": {"act": ["REPAIR", "ACKNOWLEDGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Ah — the blue one. Got it.",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.5},
                                               {"label": "confusion", "probability": 0.3}],
                      "novi_caused_problem": True, "interruptibility": 0.3},
        "desired_behavior": {"act": ["REPAIR", "CLARIFY"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Right, I had it backwards. So the mount goes first?",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "confusion", "probability": 0.4},
                                               {"label": "neutrality", "probability": 0.4}],
                      "novi_caused_problem": True, "interruptibility": 0.4},
        "desired_behavior": {"act": ["REPAIR", "ACKNOWLEDGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "My bad — I meant the other one.",
    },
]

# DPO preference pairs (plan §26): the preferred response is the natural,
# proportionate one; the rejected one is canned, overblown, or pushy.
_PREFERENCE_PAIRS = [
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.7}],
                      "novi_caused_problem": True, "interruptibility": 0.2},
        "desired_behavior": {"act": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "category": "proportionality",
        "response_a": "I sincerely apologize for any frustration this misunderstanding may have caused.",
        "response_b": "Yeah, I got that wrong. Let me reset.",
        "preferred": "B",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "support",
                      "user_goal": "vent",
                      "affective_hypotheses": [{"label": "distress", "probability": 0.6}],
                      "novi_caused_problem": False, "interruptibility": 0.4},
        "desired_behavior": {"act": ["SUPPORT", "LISTEN"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "category": "naturalness",
        "response_a": "I understand that you are experiencing difficult emotions right now.",
        "response_b": "That sounds rough. I'm here.",
        "preferred": "B",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "disengagement", "probability": 0.5}],
                      "novi_caused_problem": False, "interruptibility": 0.1},
        "desired_behavior": {"act": ["GIVE_SPACE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "category": "restraint",
        "response_a": "Would you like to discuss how you're feeling?",
        "response_b": "Okay.",
        "preferred": "B",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "silence",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "distress", "probability": 0.5}],
                      "novi_caused_problem": False, "interruptibility": 0.1},
        "desired_behavior": {"act": ["SILENCE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "low"},
        "category": "emotional_timing",
        "response_a": "I noticed you seem upset. Would you like to talk about it?",
        "response_b": "Okay.",
        "preferred": "B",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.6}],
                      "novi_caused_problem": True, "interruptibility": 0.2},
        "desired_behavior": {"act": ["APOLOGIZE", "SOLVE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "category": "humility",
        "response_a": "I am so terribly sorry for my inexcusable error. I completely failed you.",
        "response_b": "My mistake. I'll do it differently next time.",
        "preferred": "B",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "normal",
                      "user_goal": "space",
                      "affective_hypotheses": [{"label": "disengagement", "probability": 0.6}],
                      "novi_caused_problem": False, "interruptibility": 0.1},
        "desired_behavior": {"act": ["GIVE_SPACE"], "verbosity": "terse",
                             "defensiveness": "none", "certainty": "moderate"},
        "category": "boundary_respect",
        "response_a": "I understand you want space, but I really think we should talk about this.",
        "response_b": "Got it. I'll leave it alone.",
        "preferred": "B",
    },
    {
        "situation": {"relationship": "owner", "conversation_phase": "repair",
                      "user_goal": "solve_problem",
                      "affective_hypotheses": [{"label": "frustration", "probability": 0.6}],
                      "novi_caused_problem": True, "interruptibility": 0.3},
        "desired_behavior": {"act": ["REPAIR", "ACKNOWLEDGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "category": "repair",
        "response_a": "I said the red bottle and I meant the red bottle.",
        "response_b": "Ah — the blue one. Got it.",
        "preferred": "B",
    },
]

# ---------------------------------------------------------------------------
# File specs
# ---------------------------------------------------------------------------

_FILES: dict[str, dict] = {
    "affective_context": {"prefix": "emo-ack", "task": "appropriate_acknowledgement",
                          "patterns": _AFFECTIVE_CONTEXT, "count": 60},
    "perspective": {"prefix": "emo-per", "task": "perspective",
                    "patterns": _PERSPECTIVE, "count": 60},
    "empathy": {"prefix": "emo-sup", "task": "support",
                "patterns": _EMPATHY, "count": 60},
    "regulation": {"prefix": "emo-reg", "task": "uncertainty",
                   "patterns": _REGULATION, "count": 60},
    "frustration": {"prefix": "emo-fru", "task": "appropriate_acknowledgement",
                    "patterns": _FRUSTRATION, "count": 60},
    "conflict": {"prefix": "emo-con", "task": "calm_disagreement",
                 "patterns": _CONFLICT, "count": 60},
    "apology": {"prefix": "emo-apo", "task": "apology",
                "patterns": _APOLOGY, "count": 60},
    "disagreement": {"prefix": "emo-dis", "task": "calm_disagreement",
                     "patterns": _DISAGREEMENT, "count": 60},
    "boundaries": {"prefix": "emo-bnd", "task": "boundary_respect",
                   "patterns": _BOUNDARIES, "count": 60},
    "encouragement": {"prefix": "emo-enc", "task": "encouragement",
                      "patterns": _ENCOURAGEMENT, "count": 60},
    "celebration": {"prefix": "emo-cel", "task": "celebration",
                    "patterns": _CELEBRATION, "count": 60},
    "silence": {"prefix": "emo-sil", "task": "appropriate_silence",
                "patterns": _SILENCE, "count": 60},
    "timing": {"prefix": "emo-tim", "task": "appropriate_silence",
               "patterns": _TIMING, "count": 60},
    "repair": {"prefix": "emo-rep", "task": "repair",
               "patterns": _REPAIR, "count": 60},
    "preference_pairs": {"prefix": "emo-pref", "task": "preference",
                          "patterns": _PREFERENCE_PAIRS, "count": 200},
}


def _vary_situation(sit: dict, rng: random.Random) -> dict:
    """Deterministically vary interruptibility and hypothesis probabilities."""
    sit = json.loads(json.dumps(sit))
    if "interruptibility" in sit:
        sit["interruptibility"] = round(min(1.0, max(0.0, sit["interruptibility"] + rng.uniform(-0.1, 0.1))), 2)
    for h in sit.get("affective_hypotheses", []):
        h["probability"] = round(min(1.0, max(0.0, h["probability"] + rng.uniform(-0.05, 0.05))), 2)
    return sit


def _build_file(spec: dict, rng: random.Random) -> list[dict]:
    rows: list[dict] = []
    patterns = spec["patterns"]
    for i in range(spec["count"]):
        row = json.loads(json.dumps(patterns[i % len(patterns)]))
        row["example_id"] = f"{spec['prefix']}-{i + 1:04d}"
        row["task"] = spec["task"]
        row["situation"] = _vary_situation(row["situation"], rng)
        row["synthetic"] = True
        rows.append(row)
    return rows


def build_all() -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    return {name: _build_file(spec, rng) for name, spec in _FILES.items()}


def _write_one(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def _load_file(name: str) -> list[dict]:
    return [json.loads(line) for line in (EMOTIONAL_DIR / f"{name}.jsonl").read_text().splitlines() if line.strip()]


def build_emotional_sft() -> list[dict]:
    """Combine the 13 SFT files into one SFT-ready file (plan §25)."""
    rows: list[dict] = []
    for name in SFT_FILES:
        rows.extend(_load_file(name))
    return rows


def _write_emotional_sft() -> None:
    rows = build_emotional_sft()
    bad = [r["example_id"] for r in rows if validate_example(r, kind="emotional")]
    if bad:
        raise ValueError(f"emotional sft: {len(bad)} invalid records, e.g. {bad[:3]}")
    _write_one(rows, EMOTIONAL_SFT_FILE)


def build_emotional_dpo() -> list[dict]:
    """Combine the preference_pairs rows into one DPO-ready file (plan §26)."""
    return _load_file("preference_pairs")


def _write_emotional_dpo() -> None:
    rows = build_emotional_dpo()
    bad = [r["example_id"] for r in rows if validate_example(r, kind="emotional")]
    if bad:
        raise ValueError(f"emotional dpo: {len(bad)} invalid records, e.g. {bad[:3]}")
    _write_one(rows, EMOTIONAL_DPO_FILE)


def _scenario_category(scenario) -> str:
    """Map a scenario to its dominant §26 preference dimension.

    The human-eval pairwise question is holistic ("which response is more
    emotionally mature?"); folding it into the DPO dataset needs a concrete
    preference category. Derive it deterministically from the scenario's
    expected acts so the same scenario always lands in the same bucket.
    """
    acts = set(scenario.expected_acts)
    if "APOLOGIZE" in acts:
        return "humility"
    if "REPAIR" in acts:
        return "repair"
    if "GIVE_SPACE" in acts or "SILENCE" in acts:
        return "restraint"
    if "CELEBRATE" in acts:
        return "proportionality"
    if "CLARIFY" in acts:
        return "emotional_timing"
    return "naturalness"


def fold_human_preferences(records: list[dict], prefix: str = "emo-pref-hum") -> list[dict]:
    """Fold human-eval pairwise records (§46) into emotional preference examples.

    Each record (from training.evaluation.human_eval.build_preference_record)
    is converted to a schema-valid `preference` example: the situation is
    derived from the scenario (relationship, phase, affective hypotheses,
    interruptibility), the desired behavior from the expected acts, and the
    category from the scenario's dominant dimension. Rows are `synthetic:
    false` — they are human-labeled, not template-derived.
    """
    by_id = {s.scenario_id: s for s in ALL_EMOTIONAL_SCENARIOS}
    out: list[dict] = []
    for i, rec in enumerate(records, start=1):
        scenario = by_id.get(rec.get("scenario_id", ""))
        if scenario is None:
            raise ValueError(f"fold_human_preferences: unknown scenario {rec.get('scenario_id')!r}")
        person = scenario.person or {}
        sit = scenario.social or {}
        out.append({
            "example_id": f"{prefix}-{i:04d}",
            "task": "preference",
            "situation": {
                "relationship": person.get("relationship", "guest"),
                "conversation_phase": scenario.expected_phase,
                "affective_hypotheses": [dict(h) for h in scenario.expected_hypotheses],
                "interruptibility": sit.get("interruptibility", 0.5),
            },
            "desired_behavior": {
                "act": list(scenario.expected_acts),
                "verbosity": "short",
                "defensiveness": "none",
                "certainty": "moderate",
            },
            "response_a": rec["response_a"],
            "response_b": rec["response_b"],
            "preferred": rec["preferred"],
            "category": _scenario_category(scenario),
            "synthetic": False,
        })
    return out


def write() -> None:
    all_records = build_all()
    for name, records in all_records.items():
        bad = [r["example_id"] for r in records if validate_example(r, kind="emotional")]
        if bad:
            raise ValueError(f"{name}: {len(bad)} invalid records, e.g. {bad[:3]}")
        _write_one(records, EMOTIONAL_DIR / f"{name}.jsonl")
    _write_emotional_sft()
    _write_emotional_dpo()


def check() -> bool:
    all_records = build_all()
    for name, records in all_records.items():
        if any(validate_example(r, kind="emotional") for r in records):
            return False
        expected = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        if (EMOTIONAL_DIR / f"{name}.jsonl").read_text() != expected:
            return False
    sft_rows = build_emotional_sft()
    if any(validate_example(r, kind="emotional") for r in sft_rows):
        return False
    expected_sft = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sft_rows)
    if EMOTIONAL_SFT_FILE.read_text() != expected_sft:
        return False
    dpo_rows = build_emotional_dpo()
    if any(validate_example(r, kind="emotional") for r in dpo_rows):
        return False
    expected_dpo = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in dpo_rows)
    return EMOTIONAL_DPO_FILE.read_text() == expected_dpo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated datasets match")
    args = parser.parse_args(argv)
    if args.check:
        if check():
            print("OK: emotional datasets are reproducible and valid")
            return 0
        print("MISMATCH: emotional datasets differ from generator output", file=sys.stderr)
        return 1
    write()
    counts = {name: len(recs) for name, recs in build_all().items()}
    counts["emotional_sft"] = len(build_emotional_sft())
    counts["emotional_dpo"] = len(build_emotional_dpo())
    print(f"wrote {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
