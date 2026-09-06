"""Shared helpers for training pipelines (plan 23 §31)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from training.schemas import validate_example

# Short, production-parity persona for ChatML SFT. The deployed adapter was
# trained on a flat situation dump + "Communicative act: X" prompt (plan 23
# §10.2) which taught echoing/canned lines; production instead sends the LLM a
# SYSTEM persona + a structured cognitive-state block, plus the real utterance
# as USER. This constant is the training-side stand-in for that SYSTEM persona.
NOVI_PERSONA = (
    "You are Novi, a warm and grounded conversational companion. "
    "Speak naturally and plainly, like a thoughtful person in the room — never "
    "mention being an AI, a model, a system, or any internal or technical detail "
    "about yourself. Prefer the verified facts you are given about this person "
    "over your own general knowledge."
)


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


def user_utterance(example: dict[str, Any]) -> str:
    """The real user utterance for a canonical example, or '' when absent.

    Production parity (plan 03 §16): the LLM receives the actual utterance as
    the USER role, not a JSON dump. Precedence: `situation.conversation.input`
    first, then a top-level `user` key, else '' (legacy rows with no input).
    """
    sit = example.get("situation") or {}
    conv = sit.get("conversation") or {}
    inp = conv.get("input")
    if isinstance(inp, str) and inp.strip():
        return inp.strip()
    top = example.get("user")
    if isinstance(top, str) and top.strip():
        return top.strip()
    return ""


def _string_list(value: Any) -> list[str]:
    """Normalize an optional string / list-of-strings into non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def render_chatml(example: dict[str, Any]) -> tuple[str, str]:
    """Canonical example -> production-shaped (system, user) ChatML roles.

    system = NOVI_PERSONA + the situation rendered as bullet context lines
    (mirroring the brain's ``render_conversation_block`` shape: intent,
    referents, response goal, verified facts). user = the real utterance from
    ``user_utterance``. Legacy rows with no user text still render a system
    here, but ``torch_sft`` falls back to the flat prompt for them.
    """
    sit = example.get("situation") or {}
    lines: list[str] = []
    person = sit.get("person") or {}
    if person.get("id"):
        rel = str(person.get("relationship") or "").strip()
        lines.append(f"- Person: {person['id']}" + (f" ({rel})" if rel else ""))
    conv = sit.get("conversation") or {}
    if conv.get("topic"):
        lines.append(f"- Conversation topic: {conv['topic']}")
    memory = sit.get("memory") or []
    summaries = [
        str(m.get("summary", "")).strip()
        for m in memory
        if isinstance(m, dict) and str(m.get("summary", "")).strip()
    ]
    if summaries:
        lines.append(f"- Memory: {'; '.join(summaries)}")
    if sit.get("intent"):
        lines.append(f"- Intent: {sit['intent']}")
    referents = sit.get("referents") or {}
    if referents:
        pairs = [f"{k}→{v}" for k, v in list(referents.items())[:4]]
        lines.append(f"- Referents: {'; '.join(pairs)}")
    if sit.get("response_goal"):
        lines.append(f"- Response goal: {sit['response_goal']}")
    # Optional builder-added directive lines (e.g. must-include / must-avoid).
    for key in ("packet_lines", "requirements"):
        for line in _string_list(sit.get(key)):
            lines.append(f"- requirement: {line}")
    decision = example.get("decision") or {}
    act = decision.get("dialogue_act", "")
    if act:
        lines.append(f"- Communicative act: {act}")
    system = f"{NOVI_PERSONA}\n\n" + "\n".join(lines)
    return system, user_utterance(example)


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
