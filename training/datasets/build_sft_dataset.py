"""First-experiment SFT dataset builder (plan 23 §32).

Grows the hand-curated seed (70 examples) into a 500-example training set by
deterministic, template-derived expansion. Provenance is explicit on every
row: `source: "curated"` (hand-templated, reviewable) vs
`source: "template-derived"` + `derived_from` (generated from a curated row).
Both kinds pass the full dataset validation chain (schema + context with the
memory index) — the pipeline never trains on unvalidated rows.

The expansion varies *situation* fields (location, person, social state, and
topic only where the response is topic-agnostic). Responses are never
rewritten: if the natural phrasing only fits its topic (memory-grounded,
proactive, continuation), the topic is kept.

Real interaction traces replace template-derived rows as volume grows
(plan §6-§9); `synthetic: true` marks what is still generated.

Usage:
    python datasets/build_sft_dataset.py            # regenerate (idempotent)
    python datasets/build_sft_dataset.py --check    # verify committed output matches
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

from training.collection.validator import validate_example_ctx  # noqa: E402
from training.schemas import validate_example  # noqa: E402

DATASETS = Path(__file__).resolve().parent
SFT_DIR = DATASETS / "sft"
SFT_FILE = SFT_DIR / "sft_v1.jsonl"
MEMORY_INDEX_FILE = SFT_DIR / "memory_index_v2.json"
SEED_FILE = DATASETS / "curated" / "seed_dialogue_v1.jsonl"

SEED = 20260830
TARGET_COUNT = 500  # plan §32 band: 500-2,000 for the first experiment

LOCATIONS = ("office", "kitchen", "living room", "hallway", "study")
# Topics safe to vary: responses are topic-agnostic ("Yeah, that makes sense.").
_TOPIC_AGNOSTIC_TASKS = frozenset({
    "natural_dialogue", "clarification", "repair", "social_greeting", "silence_abstention",
})


def _load_seed() -> list[dict]:
    return [json.loads(line) for line in SEED_FILE.read_text().splitlines() if line.strip()]


def _deep_copy(node):
    return json.loads(json.dumps(node))


def _expand(curated: list[dict], rng: random.Random) -> list[dict]:
    out = [dict(ex, source="curated", synthetic=False) for ex in curated]
    counter = 1
    while len(out) < TARGET_COUNT:
        base = rng.choice(curated)
        if base["task"] not in _TOPIC_AGNOSTIC_TASKS and rng.random() < 0.7:
            # topic-locked templates: keep topic, vary only situation fields
            pass
        ex = _deep_copy(base)
        ex["example_id"] = f"dlg-sft-{counter:04d}"
        counter += 1
        sit = ex["situation"]
        sit["world"]["location"] = rng.choice(LOCATIONS)
        conv = sit["conversation"]
        if ex["task"] in _TOPIC_AGNOSTIC_TASKS and conv.get("topic"):
            conv["topic"] = rng.choice(("camera integration", "the coffee order", "this week's plan",
                                        "the bookshelf", "the mug", "the headphones"))
        if rng.random() < 0.3:
            sit["person"] = _deep_copy(sit["person"])
            sit["person"]["id"] = "person:anon_001"
            sit["person"]["name"] = ""
            sit["person"]["relationship"] = "guest"
            sit["person"]["confidence"] = 0.93
        if sit["memory"]:
            for m in sit["memory"]:
                m["id"] = f"mem-{rng.randint(2000, 9999)}"
        sit["social"] = dict(sit["social"])
        sit["social"]["interruptibility"] = round(rng.choice((0.05, 0.15, 0.3, 0.5, 0.8)), 2)
        ex["source"] = "template-derived"
        ex["synthetic"] = True
        ex["derived_from"] = base["example_id"]
        out.append(ex)
    return out


def build() -> list[dict]:
    rng = random.Random(SEED)
    examples = _expand(_load_seed(), rng)
    examples.sort(key=lambda ex: ex["example_id"])
    return examples


def memory_index(examples: list[dict]) -> list[str]:
    return sorted({m["id"] for ex in examples for m in ex["situation"]["memory"]})


def validate_all(examples: list[dict]) -> list[tuple[str, list[str]]]:
    index = memory_index(examples)
    failures: list[tuple[str, list[str]]] = []
    for ex in examples:
        errors = validate_example(ex) + validate_example_ctx(ex, memory_index=index)
        if errors:
            failures.append((ex["example_id"], errors))
    return failures


def write() -> None:
    examples = build()
    failures = validate_all(examples)
    if failures:
        raise ValueError(f"sft dataset invalid: {len(failures)} failures, e.g. {failures[:3]}")
    SFT_DIR.mkdir(parents=True, exist_ok=True)
    SFT_FILE.write_text("".join(json.dumps(ex, ensure_ascii=False) + "\n" for ex in examples))
    MEMORY_INDEX_FILE.write_text(json.dumps(memory_index(examples), indent=1) + "\n")


def check() -> bool:
    examples = build()
    failures = validate_all(examples)
    if failures:
        return False
    expected = "".join(json.dumps(ex, ensure_ascii=False) + "\n" for ex in examples)
    expected_index = json.dumps(memory_index(examples), indent=1) + "\n"
    return SFT_FILE.read_text() == expected and MEMORY_INDEX_FILE.read_text() == expected_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated dataset matches")
    args = parser.parse_args(argv)
    if args.check:
        if check():
            print("OK: sft dataset is reproducible and valid")
            return 0
        print("MISMATCH: sft dataset differs from generator output", file=sys.stderr)
        return 1
    write()
    print(f"wrote {len(build())} examples to {SFT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
