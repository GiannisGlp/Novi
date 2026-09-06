"""Build the evidence-based production SFT dataset v2 (plan 03 parity).

Collects ONLY empirically validated grounded replies: turns from acceptance
scenarios whose envelope ``result == "PASS"``, whose turn ``reply_source ==
"dialogue"`` (a real LLM answer, not a canned/fallback line), with non-empty
``user_text`` and ``response_text``. No invented text — every target reply
already passed the frozen benchmark's deterministic critic checks.

Each row is a canonical training example whose ``situation`` carries the same
cognitive state the brain sends the model in production (person, utterance,
entities, recalled memory, intent, referents, response goal), so the SFT prompt
mirrors the deployed prompt shape instead of the flat plan-23 dump.

Usage::

    python -m training.datasets.build_production_sft
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.schemas import validate_example  # noqa: E402

EVIDENCE_ROOT = ROOT / "docs" / "plans" / "EVIDENCE"

# Acceptance evidence directories (frozen plan-03 benchmark runs). The c133 and
# c152 families use a wildcard so any re-run under those prefixes is picked up.
EVIDENCE_DIR_PATTERNS = [
    "conversation-baseline-live-20260905-1632",
    "conversation-baseline-live-20260905-1851",
    "conversation-residual-live-20260905-183309",
    "conversation-c133-live-*",
    "conversation-c152-live-*",
]

OUT_PATH = ROOT / "training" / "datasets" / "sft" / "sft_production_v1.jsonl"

MAX_TURNS_PER_SCENARIO = 6
MAX_ENTITIES = 4
MAX_MEMORIES = 3

# Plan-03 response goals -> dialogue act. Default RESPOND.
_GOAL_TO_ACT = {
    "ANSWER_DIRECTLY": "RESPOND",
    "ASK_CLARIFICATION": "CLARIFY",
    "CORRECT": "REPAIR",
    "SLOT_ANSWER": "RESPOND",
    "ADMIT_UNCERTAINTY": "RESPOND",
    "REMEMBER": "ACKNOWLEDGE",
    "ACKNOWLEDGE": "ACKNOWLEDGE",
    "CONTINUE_SOCIAL_CONVERSATION": "CONTINUE",
    "RECOMMEND": "RESPOND",
    "SUMMARIZE": "RESPOND",
    "REASSURE": "RESPOND",
    "EXPLAIN": "RESPOND",
}
_DEFAULT_ACT = "RESPOND"

_SOCIAL_INTENTS = frozenset({"GREETING", "FAREWELL"})
_REPAIR_GOALS = frozenset({"CORRECT"})
_REPAIR_INTENTS = frozenset({"CORRECTION"})


def resolve_evidence_dirs(
    evidence_root: Path = EVIDENCE_ROOT, patterns: list[str] | None = None
) -> list[Path]:
    """Expand the evidence-dir patterns (some contain wildcards) to real dirs."""
    dirs: list[Path] = []
    for pattern in patterns or EVIDENCE_DIR_PATTERNS:
        dirs.extend(sorted(evidence_root.glob(pattern)))
    return dirs


def iter_envelopes(base_dirs: list[Path]) -> Iterator[tuple[str, dict]]:
    """Yield (dir_name, envelope) for every scenario JSON under base dirs."""
    for base in base_dirs:
        scenarios_dir = base / "scenarios"
        if not scenarios_dir.is_dir():
            continue
        for path in sorted(scenarios_dir.glob("*.json")):
            try:
                envelope = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            yield base.name, envelope


def _normalize(text: str) -> str:
    """Single-space whitespace, strip edges."""
    return re.sub(r"\s+", " ", (text or "").strip())


def _topic(turn: dict) -> str:
    rc = turn.get("retrieved_context") or {}
    packet = (rc.get("grounding") or {}).get("packet") or {}
    anchor = packet.get("anchor") or {}
    return str(anchor.get("topic") or "").strip()


def _recalled_memories(turn: dict) -> list[str]:
    """Recalled grounding memory strings, deduped and capped.

    Primary source: the packet's ``relevant_memories[].content`` (fact-class
    labelled grounded facts). Fallback: ``response_goal.required_evidence``.
    """
    rc = turn.get("retrieved_context") or {}
    packet = ((rc.get("grounding") or {}).get("packet")) or {}
    out: list[str] = []
    seen: set[str] = set()
    for mem in packet.get("relevant_memories") or []:
        content = str(mem.get("content", "")).strip() if isinstance(mem, dict) else str(mem).strip()
        if content and content.lower() not in seen:
            seen.add(content.lower())
            out.append(content)
    goal = turn.get("response_goal") or {}
    for ev in goal.get("required_evidence") or []:
        content = str(ev).strip()
        if content and content.lower() not in seen:
            seen.add(content.lower())
            out.append(content)
    return out[:MAX_MEMORIES]


def _entities(referents: dict) -> list[str]:
    """Referent resolution values, capped (plan 03 packet shape)."""
    vals = [str(v).strip() for v in (referents or {}).values() if str(v).strip()]
    return vals[:MAX_ENTITIES]


def _requirements(turn: dict) -> list[str]:
    """Directive lines (must-include / must-avoid / response requirements)."""
    goal = turn.get("response_goal") or {}
    out: list[str] = []
    for m in goal.get("must_include") or []:
        if str(m).strip():
            out.append(f"include: {str(m).strip()}")
    for m in goal.get("must_not_include") or []:
        if str(m).strip():
            out.append(f"avoid: {str(m).strip()}")
    rc = turn.get("retrieved_context") or {}
    packet = (rc.get("grounding") or {}).get("packet") or {}
    for r in packet.get("response_requirements") or []:
        if str(r).strip():
            out.append(str(r).strip())
    return out


def _dialogue_act(goal: str) -> str:
    return _GOAL_TO_ACT.get(goal, _DEFAULT_ACT)


def _pick_task(goal: str, intent: str, has_memory: bool) -> str:
    """Map a turn to an SFT task (plan 03 parity heuristics)."""
    if goal == "ASK_CLARIFICATION":
        return "clarification"
    if goal in _REPAIR_GOALS or intent in _REPAIR_INTENTS:
        return "repair"
    if has_memory:
        return "memory_grounded_response"
    if intent in _SOCIAL_INTENTS:
        return "social_greeting"
    # SLOT_ANSWER / ACKNOWLEDGE and everything else: an ordinary natural reply.
    return "natural_dialogue"


def _collect_turns(base_dirs: list[Path]) -> list[tuple[str, dict, dict]]:
    """Collect eligible (dir_name, envelope, turn) triples.

    Eligibility: envelope result == PASS, turn reply_source == "dialogue",
    non-empty response_text and non-empty user_text. Cap MAX_TURNS_PER_SCENARIO
    per scenario (deterministic, first-in-order).
    """
    collected: list[tuple[str, dict, dict]] = []
    for dir_name, envelope in iter_envelopes(base_dirs):
        if envelope.get("result") != "PASS":
            continue
        eligible: list[dict] = []
        for turn in envelope.get("conversation") or []:
            if not isinstance(turn, dict):
                continue
            if turn.get("reply_source") != "dialogue":
                continue
            if not str(turn.get("response_text") or "").strip():
                continue
            if not str(turn.get("user_text") or "").strip():
                continue
            eligible.append(turn)
        for turn in eligible[:MAX_TURNS_PER_SCENARIO]:
            collected.append((dir_name, envelope, turn))
    return collected


def _build_row(dir_name: str, envelope: dict, turn: dict, idx: int) -> dict:
    goal = str((turn.get("response_goal") or {}).get("goal") or "")
    intent = str((turn.get("intent") or {}).get("intent") or "")
    referents = turn.get("referents") or {}
    memories = _recalled_memories(turn)
    response = _normalize(str(turn.get("response_text") or ""))
    user_text = _normalize(str(turn.get("user_text") or ""))
    situation: dict[str, Any] = {
        "person": {"id": "person:unknown", "relationship": ""},
        "conversation": {
            "topic": _topic(turn),
            "input": user_text,
            "entities": _entities(referents),
        },
        "memory": [
            {
                "id": f"acc-mem-{idx}-{i}",
                "summary": s,
                "confidence": 0.9,
                "source": "acceptance",
            }
            for i, s in enumerate(memories)
        ],
        "intent": intent,
        "referents": dict(referents),
        "response_goal": goal,
    }
    requirements = _requirements(turn)
    if requirements:
        situation["requirements"] = requirements
    return {
        "example_id": f"acc-{idx}",
        "task": _pick_task(goal, intent, bool(memories)),
        "situation": situation,
        "decision": {
            "dialogue_act": _dialogue_act(goal),
            "verbosity": "short",
        },
        "response": response,
        "preferred_response": response,
        "source": f"acceptance:{dir_name}:{envelope.get('scenario', '')}:turn{turn.get('turn_index', 0)}",
        "synthetic": False,
        "evidence_git_sha": str(envelope.get("git_sha") or ""),
    }


def build_rows(base_dirs: list[Path]) -> list[dict]:
    """Collect, dedupe, build and schema-validate the production SFT rows.

    Raises ``SystemExit`` (non-zero) if any row fails ``validate_example``.
    """
    raw = _collect_turns(base_dirs)
    seen: set[tuple[str, str]] = set()
    rows: list[dict] = []
    for dir_name, envelope, turn in raw:
        user_text = _normalize(str(turn.get("user_text") or ""))
        response = _normalize(str(turn.get("response_text") or ""))
        key = (user_text.lower(), response.lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append(_build_row(dir_name, envelope, turn, len(rows) + 1))
    invalid: list[tuple[str, list[str]]] = []
    for ex in rows:
        errs = validate_example(ex, kind="canonical")
        if errs:
            invalid.append((str(ex.get("example_id")), errs))
    if invalid:
        for eid, errs in invalid[:5]:
            print(f"INVALID {eid}: {errs}", file=sys.stderr)
        raise SystemExit(f"{len(invalid)} rows fail schema validation")
    return rows


def write_rows(rows: list[dict], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for ex in rows:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(OUT_PATH), help="output JSONL path")
    parser.add_argument("--dry-run", action="store_true", help="build + validate, don't write")
    args = parser.parse_args(argv)

    base_dirs = resolve_evidence_dirs()
    rows = build_rows(base_dirs)
    histogram = dict(sorted(Counter(ex["task"] for ex in rows).items()))
    if not args.dry_run:
        write_rows(rows, Path(args.out))

    print(f"eligible turns -> rows: {len(rows)}")
    print(f"scenarios represented: {len({ex['source'].rsplit(':turn', 1)[0] for ex in rows})}")
    print("task histogram:")
    for task, count in histogram.items():
        print(f"  {task}: {count}")
    print(f"output: {args.out if not args.dry_run else '(dry-run, not written)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
