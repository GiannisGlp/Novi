"""Auxiliary training datasets (plan 23 §33/§16/§19/§22).

Deterministic builders for the second-experiment datasets:

- preference pairs  (datasets/dpo/)         1,000+ pairs, §33 categories
- retrieval records (datasets/retrieval/)   query + candidates + features
- policy records    (datasets/policy/)      state + candidates + preferred
- grounding records (datasets/grounding/)   language + candidates + cues

Every record is `synthetic: true` (template-derived) until real interaction
traces replace it (plan §6-§9) and passes its schema validator.

Usage:
    python datasets/build_aux_datasets.py            # regenerate (idempotent)
    python datasets/build_aux_datasets.py --check    # verify output matches
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

from training.schemas import validate_example  # noqa: E402

DATASETS = Path(__file__).resolve().parent
SEED_FILE = DATASETS / "curated" / "seed_dialogue_v1.jsonl"
SEED = 20260830

PREFERENCE_COUNT = 1120
RETRIEVAL_COUNT = 320
POLICY_COUNT = 320
GROUNDING_COUNT = 240

_TOPICS = ("camera integration", "the coffee order", "this week's plan",
           "the bookshelf", "the mug", "the headphones", "the plant")

# --- assistant-like (bad) phrasing vs natural (good) phrasing ----------------
_ASSISTANT_PHRASING = (
    "I acknowledge your statement.",
    "I have detected that you have entered the room.",
    "I can confirm that the object you are referencing is a coffee mug.",
    "It is nice to see you again.",
    "I understand your question and will respond accordingly.",
    "Thank you for your input. I have noted it.",
)
_NATURAL_PHRASING = ("Yeah, that makes sense.", "Hey.", "The mug?", "Got it.", "Fair enough.")


def _situation(topic: str, location: str = "office") -> dict:
    return {
        "person": {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98},
        "world": {"location": location, "perception": []},
        "conversation": {"topic": topic, "input_event": f"about {topic}"},
        "memory": [],
        "social": {"engaged": True, "interruptibility": 0.15},
    }


# ---------------------------------------------------------------------------
# Preference pairs (plan §33)
# ---------------------------------------------------------------------------

_PAIR_KINDS: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]] = {
    "naturalness": (_ASSISTANT_PHRASING, _NATURAL_PHRASING, "B"),
    "brevity": (
        ("In my analysis, considering the full context of our prior discussion, I believe it would "
         "be most appropriate to proceed with the plan we outlined, taking into account the various "
         "factors and constraints we identified earlier, while remaining flexible to adjustments.",),
        ("Yeah, let's do that.",),
        "B",
    ),
    "context": (
        ("That's interesting.",),
        ("Right, the camera — we'd gotten to the mounting part.",),
        "B",
    ),
    "memory": (
        ("I'm not sure, I don't remember anything about that.",),
        ("We decided to try the side mount first.",),
        "B",
    ),
    "clarification": (
        ("I will move it now.",),
        ("The blue one?",),
        "B",
    ),
    "initiative": (
        ("I notice that a chair in the office has been moved approximately five centimeters from its "
         "previous position, which may indicate that someone has been sitting in it recently.",),
        ("The chair moved.",),
        "B",
    ),
    "repair": (
        ("I said the red bottle and I meant the red bottle.",),
        ("Ah — the blue one. Got it.",),
        "B",
    ),
    "social_appropriateness": (
        ("Hey buddy, long time no see! Let me tell you about everything I've been doing.",),
        ("Hey.",),
        "B",
    ),
}


def _build_preference_pairs(rng: random.Random) -> list[dict]:
    pairs: list[dict] = []
    counter = 1
    topics = _TOPICS * 2
    while len(pairs) < PREFERENCE_COUNT:
        topic = topics[counter % len(topics)]
        category = list(_PAIR_KINDS)[counter % len(_PAIR_KINDS)]
        a_variants, b_variants, preferred = _PAIR_KINDS[category]
        a = rng.choice(a_variants)
        b = rng.choice(b_variants)
        pairs.append({
            "example_id": f"pref-{counter:05d}",
            "category": category,
            "situation": _situation(topic),
            "response_a": a,
            "response_b": b,
            "preferred": preferred,
            "synthetic": True,
        })
        counter += 1
    return pairs


# ---------------------------------------------------------------------------
# Retrieval records (plan §13/§16)
# ---------------------------------------------------------------------------

_RETRIEVAL_FEATURES = ("semantic", "temporal", "person", "situation", "goal", "causal",
                       "importance", "confidence", "provenance", "spatial", "novelty")


def _candidate(text: str, **feats: float) -> tuple[str, dict]:
    return text, {f: round(feats.get(f, 0.1), 3) for f in _RETRIEVAL_FEATURES}


def _build_retrieval(rng: random.Random) -> list[dict]:
    records: list[dict] = []
    for i in range(RETRIEVAL_COUNT):
        topic = _TOPICS[i % len(_TOPICS)]
        base = topic.split()[-1] if "the " in topic else topic
        relevant = f"Vano and Novi discussed {topic} yesterday."
        cands: list[tuple[str, dict]] = [
            _candidate(relevant, semantic=0.92, temporal=0.85, situation=0.8, goal=0.7,
                       causal=0.6, importance=0.75, confidence=0.95, provenance=0.9, spatial=0.3, novelty=0.4),
            _candidate(f"Vano bought a {base} in March.", semantic=0.4, temporal=0.15, situation=0.3,
                       goal=0.2, causal=0.2, importance=0.4, confidence=0.8, provenance=0.7, spatial=0.2, novelty=0.3),
            _candidate(f"Novi saw a {base} in the kitchen.", semantic=0.35, temporal=0.5, situation=0.25,
                       goal=0.15, causal=0.1, importance=0.3, confidence=0.85, provenance=0.8, spatial=0.9, novelty=0.7),
            _candidate("The plant needs watering.", semantic=0.1, temporal=0.3, situation=0.1,
                       goal=0.1, causal=0.1, importance=0.2, confidence=0.9, provenance=0.6, spatial=0.1, novelty=0.5),
        ]
        candidates = [text for text, _f in cands]
        features = [feat for _t, feat in cands]
        records.append({
            "example_id": f"ret-{i + 1:04d}",
            "query": f"What did we decide about {topic}?",
            "candidates": candidates,
            "candidate_features": features,
            "preferred": [0],
            "synthetic": True,
        })
    return records


# ---------------------------------------------------------------------------
# Policy records (plan §12/§19)
# ---------------------------------------------------------------------------

_POLICY_PATTERNS: list[tuple[dict, list[str], str]] = [
    ({"user_speaking": False, "known_person": True, "new_event": True, "event_salience": 0.8,
      "open_thread": False, "interruption_cost": 0.1, "person_available": True,
      "social_opportunity": 0.8, "proactive_elapsed_norm": 0.33}, ["SILENCE", "GREETING", "RESPOND"], "GREETING"),
    ({"user_speaking": False, "known_person": True, "new_event": True, "event_salience": 0.75,
      "open_thread": True, "interruption_cost": 0.2, "person_available": True,
      "social_opportunity": 0.6, "proactive_elapsed_norm": 0.33}, ["SILENCE", "CONTINUE", "RESPOND"], "CONTINUE"),
    ({"user_speaking": False, "known_person": True, "new_event": True, "event_salience": 0.25,
      "open_thread": False, "interruption_cost": 0.3, "person_available": True,
      "social_opportunity": 0.3, "proactive_elapsed_norm": 0.05}, ["COMMENT", "SILENCE", "RESPOND"], "SILENCE"),
    ({"user_speaking": False, "known_person": True, "new_event": False, "event_salience": 0.0,
      "open_thread": False, "interruption_cost": 0.95, "person_available": False,
      "social_opportunity": 0.0, "proactive_elapsed_norm": 0.02}, ["COMMENT", "SILENCE"], "SILENCE"),
    ({"user_speaking": True, "known_person": True, "new_event": False, "event_salience": 0.0,
      "open_thread": False, "interruption_cost": 0.4, "person_available": True,
      "social_opportunity": 0.4, "proactive_elapsed_norm": 0.07}, ["RESPOND", "SILENCE", "COMMENT"], "RESPOND"),
    ({"user_speaking": False, "known_person": False, "new_event": True, "event_salience": 0.6,
      "open_thread": False, "interruption_cost": 0.2, "person_available": True,
      "social_opportunity": 0.5, "proactive_elapsed_norm": 0.17}, ["GREETING", "ASK", "SILENCE"], "ASK"),
    ({"user_speaking": False, "known_person": True, "new_event": True, "event_salience": 0.9,
      "open_thread": False, "interruption_cost": 0.1, "person_available": True,
      "social_opportunity": 0.9, "proactive_elapsed_norm": 0.5}, ["SILENCE", "COMMENT", "SUGGEST"], "COMMENT"),
    ({"user_speaking": False, "known_person": True, "new_event": True, "event_salience": 0.95,
      "open_thread": False, "interruption_cost": 0.05, "person_available": True,
      "social_opportunity": 0.95, "proactive_elapsed_norm": 0.33}, ["COMMENT", "WARN", "SILENCE"], "WARN"),
]


def _build_policy(rng: random.Random) -> list[dict]:
    records: list[dict] = []
    for i in range(POLICY_COUNT):
        state, candidates, preferred = _POLICY_PATTERNS[i % len(_POLICY_PATTERNS)]
        state = dict(state)
        state["event_salience"] = round(min(1.0, max(0.0, state["event_salience"] + rng.uniform(-0.08, 0.08))), 3)
        records.append({
            "example_id": f"pol-{i + 1:04d}",
            "state": state,
            "candidates": list(candidates),
            "preferred": preferred,
            "synthetic": True,
        })
    return records


# ---------------------------------------------------------------------------
# Grounding records (plan §14/§22)
# ---------------------------------------------------------------------------

_GROUNDING_PATTERNS: list[dict] = [
    {"language": "Move that there.", "candidates": ["blue mug", "red book", "laptop"],
     "cues": {"gaze": "blue mug", "pointing": "blue mug"},
     "destination_candidates": ["shelf", "table"], "gesture": "shelf",
     "preferred": "move(blue mug, shelf)"},
    {"language": "Hand me the thing on the left.", "candidates": ["plant", "blue mug", "camera"],
     "cues": {"gaze": "plant"}, "destination_candidates": [], "gesture": "",
     "preferred": "take(plant)"},
    {"language": "Is that the one we fixed?", "candidates": ["camera", "laptop", "headphones"],
     "cues": {"gaze": "camera"}, "destination_candidates": [], "gesture": "",
     "preferred": "refer(camera)"},
    {"language": "Put it next to the other one.", "candidates": ["book", "mug", "plant"],
     "cues": {"pointing": "book"}, "destination_candidates": ["desk", "shelf"], "gesture": "desk",
     "preferred": "move(book, desk)"},
]


def _build_grounding(rng: random.Random) -> list[dict]:
    records: list[dict] = []
    for i in range(GROUNDING_COUNT):
        base = _GROUNDING_PATTERNS[i % len(_GROUNDING_PATTERNS)]
        rec = json.loads(json.dumps(base))
        rec["example_id"] = f"gr-{i + 1:04d}"
        rec["synthetic"] = True
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------

_BUILDERS = {
    "dpo": (_build_preference_pairs, DATASETS / "dpo" / "preference_pairs_v1.jsonl", "preference"),
    "retrieval": (_build_retrieval, DATASETS / "retrieval" / "retrieval_v1.jsonl", "retrieval"),
    "policy": (_build_policy, DATASETS / "policy" / "policy_v1.jsonl", "policy"),
    "grounding": (_build_grounding, DATASETS / "grounding" / "grounding_v1.jsonl", "grounding"),
}


def build_all() -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    return {name: builder(rng) for name, (builder, _p, _k) in _BUILDERS.items()}


def _write_one(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def write() -> None:
    all_records = build_all()
    for name, (_builder, path, kind) in _BUILDERS.items():
        records = all_records[name]
        bad = [r["example_id"] for r in records if validate_example(r, kind=kind)]
        if bad:
            raise ValueError(f"{name}: {len(bad)} invalid records, e.g. {bad[:3]}")
        _write_one(records, path)


def check() -> bool:
    all_records = build_all()
    for name, (_builder, path, kind) in _BUILDERS.items():
        records = all_records[name]
        if any(validate_example(r, kind=kind) for r in records):
            return False
        expected = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        if path.read_text() != expected:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated datasets match")
    args = parser.parse_args(argv)
    if args.check:
        if check():
            print("OK: aux datasets are reproducible and valid")
            return 0
        print("MISMATCH: aux datasets differ from generator output", file=sys.stderr)
        return 1
    write()
    counts = {name: len(recs) for name, recs in build_all().items()}
    print(f"wrote {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
