"""Shared helpers for training pipelines (plan 23 §31)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from training.schemas import validate_example


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"dataset not found: {p}")
    out: list[dict[str, Any]] = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def situation_to_prompt(example: dict[str, Any]) -> str:
    """Canonical example -> SFT prompt (situation + communicative act context).

    Training target (plan §10.2): situation + communicative act -> natural
    response. NOT raw user text -> generic chatbot answer.
    """
    sit = example.get("situation") or {}
    person = sit.get("person") or {}
    parts = []
    if person.get("id"):
        parts.append(f"Person: {person.get('id')} ({person.get('relationship', '')})")
    if sit.get("world"):
        parts.append(f"World: {json.dumps(sit['world'], ensure_ascii=False)}")
    if sit.get("conversation"):
        parts.append(f"Conversation: {json.dumps(sit['conversation'], ensure_ascii=False)}")
    if sit.get("memory"):
        parts.append(f"Memory: {json.dumps(sit['memory'], ensure_ascii=False)}")
    if sit.get("social"):
        parts.append(f"Social: {json.dumps(sit['social'], ensure_ascii=False)}")
    decision = example.get("decision") or {}
    act = decision.get("dialogue_act", "")
    return "\n".join(parts + [f"Communicative act: {act}"])


def emotional_situation_to_prompt(example: dict[str, Any]) -> str:
    """Emotional example -> SFT prompt (social context + selected strategy).

    Training target (plan 24 §25): social context + selected strategy -> natural
    response. NOT emotion label -> canned phrase. The affective hypotheses are
    rendered as probabilistic context (the emotional signal is not a fact), and
    the selected strategy is the first acceptable act in desired_behavior.
    """
    sit = example.get("situation") or {}
    parts = []
    if sit.get("relationship"):
        parts.append(f"Relationship: {sit['relationship']}")
    if sit.get("conversation_phase"):
        parts.append(f"Conversation phase: {sit['conversation_phase']}")
    if sit.get("user_goal"):
        parts.append(f"User goal: {sit['user_goal']}")
    if sit.get("affective_hypotheses"):
        parts.append(f"Affective hypotheses: {json.dumps(sit['affective_hypotheses'], ensure_ascii=False)}")
    if "novi_caused_problem" in sit:
        parts.append(f"Novi caused problem: {str(sit['novi_caused_problem']).lower()}")
    if "interruptibility" in sit:
        parts.append(f"Interruptibility: {sit['interruptibility']}")
    beh = example.get("desired_behavior") or {}
    acts = beh.get("act") or []
    act = acts[0] if acts else ""
    return "\n".join(parts + [f"Communicative act: {act}"])


def prompt_for(example: dict[str, Any]) -> str:
    """Dispatch to the right prompt builder by example kind.

    Emotional examples (plan 24 §24) carry `desired_behavior` and use the
    emotional prompt; plan-23 examples use the canonical situation prompt.
    """
    if "desired_behavior" in example:
        return emotional_situation_to_prompt(example)
    return situation_to_prompt(example)


def task_counts(examples: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(ex.get("task", "unknown") for ex in examples).items()))


def emit_report(report: dict[str, Any], out_json: str | None) -> int:
    """Write the final JSON report: to a file, or one line to stdout with '-'."""
    payload = json.dumps(report, ensure_ascii=False, indent=2 if out_json not in (None, "-") else None)
    if out_json == "-":
        print(payload)
    elif out_json:
        Path(out_json).write_text(payload + "\n")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True, help="committed YAML config under training/configs/")
    parser.add_argument("--out-json", default=None, help="write report JSON here, or '-' for stdout")
    parser.add_argument("--dry-run", action="store_true", default=False, help="deterministic smoke run without a model")


def check_min_examples(examples: list[dict[str, Any]], minimum: int, kind: str) -> None:
    if len(examples) < minimum:
        print(
            f"SKIP: {kind} requires >= {minimum} curated examples "
            f"(have {len(examples)}); collect more traces first (plan §32)",
            file=sys.stderr,
        )
        raise SystemExit(0)
    _validate_schema(examples, kind)


def _validate_schema(examples: list[dict[str, Any]], kind: str) -> None:
    # Emotional examples (plan 24) carry desired_behavior and validate as
    # `emotional`; plan-23 examples validate as `canonical`.
    schema_kind = "emotional" if any("desired_behavior" in ex for ex in examples) else "canonical"
    bad = [(ex.get("example_id"), validate_example(ex, kind=schema_kind)) for ex in examples]
    bad = [(eid, errs) for eid, errs in bad if errs]
    if bad:
        raise ValueError(f"{kind}: {len(bad)} examples fail schema validation, e.g. {bad[:3]}")
