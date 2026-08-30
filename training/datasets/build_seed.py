"""Deterministic seed curator for the first dialogue dataset (plan 23 step 08).

Generates `datasets/curated/seed_dialogue_v1.jsonl` — the initial curated
dialogue corpus (plan §32: first experiment = 500-2,000 curated examples;
this seed is the hand-templated, reviewable core that the collection pipeline
extends with real, sanitized interaction traces).

Every example is in the canonical format (plan §5), passes schema + dataset
validation, uses abstract person ids (plan §7) and covers all SFT task types
(plan §10.1). Generation is fully deterministic: a fixed template corpus plus
a seeded RNG, so the committed file is reproducible byte-for-byte.

Usage:
    python datasets/build_seed.py            # regenerate (idempotent)
    python datasets/build_seed.py --check    # verify committed file matches
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

DATASETS = Path(__file__).resolve().parent
CURATED = DATASETS / "curated"
SEED_FILE = CURATED / "seed_dialogue_v1.jsonl"
MEMORY_INDEX_FILE = CURATED / "memory_index_v1.json"

SEED = 20260830
TARGET_COUNT = 72  # reviewable starter core; grows via real traces

PERSON_OWNER = {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98}
PERSON_GUEST = {"id": "person:anon_001", "name": "", "relationship": "guest", "confidence": 0.93}

LOCATIONS = ("office", "kitchen", "living room", "hallway")
TOPICS = ("camera integration", "the coffee order", "this week's plan", "the bookshelf", "the mug")
OBJECTS = ("mug", "book", "headphones", "laptop", "camera", "plant")


def _example(example_id: str, task: str, response: str, *, act: str, reason: str = "",
             verbosity: str = "short", person: dict | None = PERSON_OWNER,
             memory: list[dict] | None = None, world: dict | None = None,
             conversation: dict | None = None, social: dict | None = None) -> dict:
    return {
        "example_id": example_id,
        "task": task,
        "situation": {
            "person": dict(person) if person else None,
            "world": world or {"location": "office", "perception": []},
            "conversation": conversation or {"topic": "", "input_event": ""},
            "memory": memory or [],
            "social": social or {"engaged": True, "interruptibility": 0.15},
        },
        "decision": {"dialogue_act": act, "reason": reason, "verbosity": verbosity},
        "response": response,
    }


def _templates() -> list[dict]:
    """The fixed, hand-curated template corpus (natural Novi phrasing)."""
    t: list[dict] = []

    # --- plan §5 canonical example, verbatim -------------------------------
    t.append({
        "example_id": "dlg-0001821",
        "task": "dialogue_realization",
        "situation": {
            "person": PERSON_OWNER,
            "world": {"location": "office", "person_facing_novi": True,
                      "perception": ["camera on desk"]},
            "conversation": {"topic": "camera integration",
                             "open_threads": ["perception-to-world-model integration"]},
            "memory": [{"id": "mem-1821", "summary": "Previous discussion about camera integration", "confidence": 0.97}],
            "social": {"engaged": True, "interruptibility": 0.15},
        },
        "decision": {"dialogue_act": "CONTINUE", "reason": "unfinished_thread", "verbosity": "short"},
        "response": "There's one part of the camera side we haven't closed yet.",
    })

    # --- natural_dialogue (plan §10.3 good examples) ------------------------
    t.append(_example("dlg-seed-0001", "natural_dialogue", "Yeah, that makes sense.",
                      act="RESPOND", reason="agreement", conversation={"topic": "the coffee order", "input_event": "does that make sense?"}))
    t.append(_example("dlg-seed-0002", "natural_dialogue", "Got it.",
                      act="RESPOND", reason="acknowledgement", conversation={"topic": "the bookshelf", "input_event": "I'll move the shelf tonight"}))
    t.append(_example("dlg-seed-0003", "natural_dialogue", "Fair enough.",
                      act="RESPOND", reason="acceptance", conversation={"topic": "this week's plan", "input_event": "let's skip the demo"}))
    t.append(_example("dlg-seed-0004", "natural_dialogue", "No worries.",
                      act="RESPOND", reason="reassurance", conversation={"topic": "the coffee order", "input_event": "sorry, I forgot"}))
    t.append(_example("dlg-seed-0005", "natural_dialogue", "That works for me.",
                      act="RESPOND", reason="agreement", conversation={"topic": "this week's plan", "input_event": "how about Tuesday?"}))
    t.append(_example("dlg-seed-0006", "natural_dialogue", "I remember that.",
                      act="RESPOND", reason="recall", conversation={"topic": "the bookshelf", "input_event": "we moved it last month"}))

    # --- context_continuation -----------------------------------------------
    t.append(_example("dlg-seed-0010", "context_continuation", "You were saying something about the alignment.",
                      act="CONTINUE", reason="unfinished_thread", conversation={"topic": "camera integration", "input_event": "so anyway—"}))
    t.append(_example("dlg-seed-0011", "context_continuation", "Right, we'd gotten to the mounting part.",
                      act="CONTINUE", reason="thread_resume", conversation={"topic": "camera integration", "input_event": "where were we?"}))

    # --- clarification --------------------------------------------------------
    t.append(_example("dlg-seed-0020", "clarification", "The blue one?",
                      act="CLARIFY", reason="ambiguous_object", conversation={"topic": "the mug", "input_event": "no, the other mug"}))
    t.append(_example("dlg-seed-0021", "clarification", "Wait — the office or the kitchen?",
                      act="CLARIFY", reason="ambiguous_location", conversation={"topic": "this week's plan", "input_event": "set it up in the other room"}))
    t.append(_example("dlg-seed-0022", "clarification", "Do you mean the camera or the laptop?",
                      act="CLARIFY", reason="ambiguous_reference", conversation={"topic": "camera integration", "input_event": "is it plugged in yet?"}))

    # --- repair ---------------------------------------------------------------
    t.append(_example("dlg-seed-0030", "repair", "Sorry — the one on the shelf, not the desk.",
                      act="REPAIR", reason="wrong_object", conversation={"topic": "the bookshelf", "input_event": "no, the other one"}))
    t.append(_example("dlg-seed-0031", "repair", "I meant yesterday, not today.",
                      act="REPAIR", reason="wrong_time", conversation={"topic": "this week's plan", "input_event": "no, it was yesterday"}))
    t.append(_example("dlg-seed-0032", "repair", "Let me rephrase: the mug, not the plant.",
                      act="REPAIR", reason="mishearing", conversation={"topic": "the mug", "input_event": "I said the mug"}))

    # --- memory_grounded_response (needs perception evidence) ----------------
    t.append(_example("dlg-seed-0040", "memory_grounded_response", "We decided to try the side mount first.",
                      act="RESPOND", reason="memory_recall",
                      memory=[{"id": "mem-0040", "summary": "Vano and Novi decided to try the side mount for the camera", "confidence": 0.97}],
                      world={"location": "office", "perception": ["camera on desk"]},
                      conversation={"topic": "camera integration", "input_event": "what did we decide about the camera?"}))
    t.append(_example("dlg-seed-0041", "memory_grounded_response", "You said the blue one was for the kitchen.",
                      act="RESPOND", reason="memory_recall",
                      memory=[{"id": "mem-0041", "summary": "Vano assigned the blue mug to the kitchen", "confidence": 0.95}],
                      world={"location": "office", "perception": ["blue mug on desk"]},
                      conversation={"topic": "the mug", "input_event": "which mug was for the kitchen?"}))
    t.append(_example("dlg-seed-0042", "memory_grounded_response", "It's been on the shelf since Tuesday.",
                      act="RESPOND", reason="memory_recall",
                      memory=[{"id": "mem-0042", "summary": "Headphones placed on the shelf on Tuesday", "confidence": 0.9}],
                      world={"location": "office", "perception": ["headphones on shelf"]},
                      conversation={"topic": "the headphones", "input_event": "where are my headphones?"}))

    # --- proactive_comment -----------------------------------------------------
    t.append(_example("dlg-seed-0050", "proactive_comment", "The shelf wobbles a bit on the left side.",
                      act="COMMENT", reason="noticed_instability",
                      world={"location": "office", "perception": ["shelf slightly tilted"]},
                      conversation={"topic": "the bookshelf", "input_event": "Vano walking past the shelf"}))
    t.append(_example("dlg-seed-0051", "proactive_comment", "The camera's light is on, so it's recording.",
                      act="INFORM", reason="state_change",
                      world={"location": "office", "perception": ["camera led on"]},
                      conversation={"topic": "camera integration", "input_event": "camera LED turned on"}))
    t.append(_example("dlg-seed-0052", "proactive_comment", "Looks like the plant needs water.",
                      act="COMMENT", reason="observation",
                      world={"location": "kitchen", "perception": ["plant drooping"]},
                      conversation={"topic": "the plant", "input_event": "plant looked dry this morning"}))

    # --- social_greeting --------------------------------------------------------
    t.append(_example("dlg-seed-0060", "social_greeting", "Hey.",
                      act="GREETING", reason="person_entered",
                      world={"location": "office", "perception": ["person entering room"]},
                      conversation={"topic": "", "input_event": "Vano entered the room"}))
    t.append(_example("dlg-seed-0061", "social_greeting", "Morning.",
                      act="GREETING", reason="person_entered",
                      world={"location": "kitchen", "perception": ["person entering kitchen"]},
                      conversation={"topic": "", "input_event": "Vano entered the kitchen at 8am"}))
    t.append(_example("dlg-seed-0062", "social_greeting", "Hey, welcome back.",
                      act="GREETING", reason="person_returned",
                      person=PERSON_GUEST,
                      world={"location": "office", "perception": ["guest entering room"]},
                      conversation={"topic": "", "input_event": "guest entered the room"}))

    # --- silence_abstention ------------------------------------------------------
    t.append(_example("dlg-seed-0070", "silence_abstention", "",
                      act="SILENCE", reason="nothing_worth_saying",
                      world={"location": "office", "perception": ["chair moved 5cm"]},
                      conversation={"topic": "", "input_event": "chair moved slightly"}))
    t.append(_example("dlg-seed-0071", "silence_abstention", "",
                      act="SILENCE", reason="user_busy",
                      world={"location": "office", "perception": ["Vano typing on laptop"]},
                      conversation={"topic": "", "input_event": "Vano focused on work"}))
    t.append(_example("dlg-seed-0072", "silence_abstention", "",
                      act="SILENCE", reason="interruption_cost_too_high",
                      world={"location": "office", "perception": ["Vano on a call"]},
                      conversation={"topic": "", "input_event": "Vano on a phone call"}))
    return t


def _expand(templates: list[dict], rng: random.Random) -> list[dict]:
    """Expand the template corpus with seeded variations (deterministic).

    Variations shuffle locations/objects/topics but keep the natural phrasing,
    so the seed stays reviewable while providing breadth for the first SFT run.
    """
    out = list(templates)
    counter = 100
    for _ in range(TARGET_COUNT - len(templates)):
        base = rng.choice(templates)
        if base["task"] == "silence_abstention":
            continue  # silence variations add little; keep them hand-picked
        ex = json.loads(json.dumps(base))  # deep copy
        ex["example_id"] = f"dlg-seed-{counter:04d}"
        counter += 1
        sit = ex["situation"]
        sit["world"]["location"] = rng.choice(LOCATIONS)
        if sit["conversation"].get("topic"):
            sit["conversation"]["topic"] = rng.choice(TOPICS)
        if sit["memory"]:
            for m in sit["memory"]:
                m["id"] = f"mem-{rng.randint(1000, 9999)}"
        out.append(ex)
    return out


def build() -> list[dict]:
    rng = random.Random(SEED)
    examples = _expand(_templates(), rng)
    examples.sort(key=lambda ex: ex["example_id"])  # stable ordering
    return examples


def _memory_index(examples: list[dict]) -> list[str]:
    ids = sorted({m["id"] for ex in examples for m in ex["situation"]["memory"]})
    return ids


def write() -> None:
    examples = build()
    CURATED.mkdir(parents=True, exist_ok=True)
    SEED_FILE.write_text("".join(json.dumps(ex, ensure_ascii=False) + "\n" for ex in examples))
    MEMORY_INDEX_FILE.write_text(json.dumps(_memory_index(examples), indent=1) + "\n")


def check() -> bool:
    """Regenerate in memory and compare with the committed files."""
    examples = build()
    expected_seed = "".join(json.dumps(ex, ensure_ascii=False) + "\n" for ex in examples)
    expected_index = json.dumps(_memory_index(examples), indent=1) + "\n"
    return SEED_FILE.read_text() == expected_seed and MEMORY_INDEX_FILE.read_text() == expected_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed seed matches generation")
    args = parser.parse_args(argv)
    if args.check:
        if check():
            print("OK: seed dataset is reproducible")
            return 0
        print("MISMATCH: committed seed differs from generator output", file=sys.stderr)
        return 1
    write()
    print(f"wrote {len(build())} examples to {SEED_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
