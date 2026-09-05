"""Human acceptance-session grading (plan 03 Phases 23-24, form Phase 36).

A real 20-30 minute session is recorded as Step 0.2 interaction JSONL
(``conversation_replay --interaction-log`` or the live
``interaction_log_path``). This tool turns that log into:

1. ``template`` — one grade sheet row per response with empty human
   fields (grade, failure labels, root cause, corrections);
2. ``apply`` — merges the human-filled sheet back into graded session
   evidence with PASS/MINOR/MAJOR/FAIL counts and a root-cause
   histogram driving the Phase 24 root-cause loop.

Grades are constrained to the Phase 23 scale; root causes to the
Phase 24 layer list (unknown layers are kept but flagged).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

GRADES = ("PASS", "MINOR ISSUE", "MAJOR ISSUE", "FAIL")

# Plan Phase 24 possible root layers.
ROOT_LAYERS = (
    "ASR",
    "input normalization",
    "intent",
    "referent resolution",
    "conversation state",
    "memory retrieval",
    "world retrieval",
    "emotion/social state",
    "context composition",
    "response planning",
    "model routing",
    "LLM generation",
    "response critic",
    "repair",
    "persistence",
)


def load_log_records(log_path: str | Path) -> list[dict[str, Any]]:
    """Read Step 0.2 interaction JSONL records (skips blank lines)."""
    records: list[dict[str, Any]] = []
    for line in Path(log_path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def grade_template(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One empty grade row per recorded response."""
    rows: list[dict[str, Any]] = []
    for record in records:
        intent = record.get("intent")
        rows.append({
            "conversation_id": record.get("conversation_id", ""),
            "turn_id": record.get("turn_id", 0),
            "user_text": record.get("raw_input", ""),
            "response": record.get("response", ""),
            "reply_source": record.get("reply_source", ""),
            "intent": (intent or {}).get("intent", "") if isinstance(intent, dict) else "",
            "grade": None,
            "failure_labels": [],
            "root_cause": "",
            "what_wrong": "",
            "what_instead": "",
        })
    return rows


def apply_grades(records: list[dict[str, Any]],
                 rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge filled grade rows into graded session evidence."""
    # Occurrence-ordered matching: a log can hold two runs appended
    # together (or a resumed session), so duplicate keys match in order
    # instead of the last row silently winning.
    by_turn: dict[tuple[str, Any], list[dict[str, Any]]] = {}
    for row in rows:
        if isinstance(row, dict):
            by_turn.setdefault(
                (str(row.get("conversation_id", "")), row.get("turn_id")),
                []).append(row)
    graded_turns: list[dict[str, Any]] = []
    grade_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    root_counts: dict[str, int] = {}
    unknown_roots: list[str] = []
    for record in records:
        key = (str(record.get("conversation_id", "")), record.get("turn_id"))
        queue = by_turn.get(key, [])
        row = queue.pop(0) if queue else {}
        grade = str(row.get("grade") or "UNGRADED")
        if grade not in GRADES:
            grade = "UNGRADED"
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        labels = [str(label) for label in (row.get("failure_labels") or [])]
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        root = str(row.get("root_cause") or "")
        if root:
            root_counts[root] = root_counts.get(root, 0) + 1
            if root not in ROOT_LAYERS and root not in unknown_roots:
                unknown_roots.append(root)
        graded_turns.append({
            "conversation_id": record.get("conversation_id", ""),
            "turn_id": record.get("turn_id", 0),
            "user_text": record.get("raw_input", ""),
            "response": record.get("response", ""),
            "intent": record.get("intent"),
            "grade": grade,
            "failure_labels": labels,
            "root_cause": root,
            "what_wrong": str(row.get("what_wrong") or ""),
            "what_instead": str(row.get("what_instead") or ""),
        })
    return {
        "schema": "conversation-session-grades/v1",
        "turns": len(records),
        "graded": sum(grade_counts.get(g, 0) for g in GRADES),
        "grade_counts": grade_counts,
        "label_counts": dict(sorted(label_counts.items(), key=lambda kv: -kv[1])),
        "root_cause_counts": dict(sorted(root_counts.items(), key=lambda kv: -kv[1])),
        "unknown_root_causes": unknown_roots,
        "graded_turns": graded_turns,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Human acceptance-session grading (plan 03 Phases 23-24)")
    sub = parser.add_subparsers(dest="command", required=True)
    template = sub.add_parser("template", help="emit an empty grade sheet for a session log")
    template.add_argument("--log", required=True, help="Step 0.2 interaction JSONL path")
    template.add_argument("--out", required=True, help="output JSONL grade sheet path")
    apply = sub.add_parser("apply", help="merge a filled grade sheet into session evidence")
    apply.add_argument("--log", required=True, help="Step 0.2 interaction JSONL path")
    apply.add_argument("--grades", required=True, help="filled grade sheet JSONL path")
    apply.add_argument("--out", required=True, help="output graded session JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "template":
        rows = grade_template(load_log_records(args.log))
        with Path(args.out).open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        print(json.dumps({"rows": len(rows)}))
        return 0
    if args.command == "apply":
        rows = [json.loads(line) for line in Path(args.grades).read_text().splitlines()
                if line.strip()]
        evidence = apply_grades(load_log_records(args.log), rows)
        Path(args.out).write_text(json.dumps(evidence, indent=2))
        print(json.dumps({key: evidence[key] for key in
                          ("turns", "graded", "grade_counts", "root_cause_counts")},
                         indent=2))
        return 0
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
