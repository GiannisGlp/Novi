"""Pairwise old-vs-new evaluation (plan 03 Phase 16).

Every intelligence change is evaluated against the previous Novi by
replaying the SAME scenarios (same input, same initial state, same
configuration where possible) and comparing. Because two checkouts
cannot share one Python process, the flow is evidence-based:

1. run ``conversation_replay --evidence-dir <old>`` on the base commit;
2. run it again with the change into ``<new>``;
3. ``conversation_pairwise compare --old <old> --new <new> --out <dir>``.

The comparison is deterministic (verdict deltas, changed responses) and
emits a human-rating template (Phase 36 questions) for the conversational
quality half that automation cannot judge. ``collect`` merges filled
ratings into preference counts. Never use a single automated score as
the only quality metric (plan §17).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Phase 36 real-user evaluation questions (null = unanswered).
RATING_QUESTIONS: dict[str, Any] = {
    "understood": None,      # 1-5 Did Novi understand what you meant?
    "on_topic": None,        # 1-5 Did it stay on the current topic?
    "remembered": None,      # 1-5 Did it remember useful context?
    "useful": None,          # 1-5 Was the answer actually useful?
    "natural": None,         # 1-5 Did it feel natural?
    "tone": None,            # 1-5 Was the emotional tone appropriate?
    "made_repeat": None,     # yes/no Did it make you repeat yourself?
    "hallucinated": None,    # yes/no Did it hallucinate anything?
    "unnecessary_question": None,  # yes/no Did it ask an unnecessary question?
    "trust": None,           # 1-5 Would you trust this response?
    "preference": None,      # "old" | "new" | "tie": which would you prefer?
    "what_wrong": "",        # What was wrong, if anything?
    "what_instead": "",      # What should Novi have said instead?
    "what_info": "",         # What information should Novi have used?
}

_SCORE_KEYS = ("understood", "on_topic", "remembered", "useful",
               "natural", "tone", "trust")


def _load_envelope(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def load_evidence_dir(directory: str | Path) -> dict[str, dict[str, Any]]:
    """Map scenario_id -> evidence envelope for one replay run."""
    directory = Path(directory)
    out: dict[str, dict[str, Any]] = {}
    for path in sorted((directory / "scenarios").glob("*.json")):
        envelope = _load_envelope(path)
        if isinstance(envelope, dict) and envelope.get("scenario"):
            out[str(envelope["scenario"])] = envelope
    return out


def _turns(envelope: dict[str, Any]) -> list[dict[str, Any]]:
    turns = envelope.get("conversation")
    return list(turns) if isinstance(turns, list) else []


def compare_scenario(old: dict[str, Any],
                     new: dict[str, Any]) -> dict[str, Any]:
    """Diff one scenario across two runs (same input, two Novis)."""
    old_turns = _turns(old)
    new_turns = _turns(new)
    turn_diffs: list[dict[str, Any]] = []
    changed = 0
    for index, (old_turn, new_turn) in enumerate(zip(old_turns, new_turns)):
        old_text = str(old_turn.get("response_text") or "")
        new_text = str(new_turn.get("response_text") or "")
        old_labels = sorted(old_turn.get("failure_labels") or [])
        new_labels = sorted(new_turn.get("failure_labels") or [])
        if old_text != new_text or old_labels != new_labels:
            changed += 1
        turn_diffs.append({
            "turn_index": index,
            "user_text": str(new_turn.get("user_text") or old_turn.get("user_text") or ""),
            "old_response": old_text,
            "new_response": new_text,
            "response_changed": old_text != new_text,
            "old_labels": old_labels,
            "new_labels": new_labels,
            "old_result": old_turn.get("result"),
            "new_result": new_turn.get("result"),
        })
    old_result = old.get("result")
    new_result = new.get("result")
    if old_result == "FAIL" and new_result == "PASS":
        delta = "fixed"
    elif old_result == "PASS" and new_result == "FAIL":
        delta = "regressed"
    elif old_result == new_result:
        delta = "stable"
    else:
        delta = "mixed"
    return {
        "scenario": str(new.get("scenario") or old.get("scenario")),
        "title": str(new.get("title") or old.get("title") or ""),
        "dimension": str(new.get("dimension") or old.get("dimension") or ""),
        "old_result": old_result,
        "new_result": new_result,
        "delta": delta,
        "turns_changed": changed,
        "turns": turn_diffs,
    }


def compare_runs(old_dir: str | Path, new_dir: str | Path) -> dict[str, Any]:
    """Compare two evidence dirs. Returns the pairwise report."""
    old = load_evidence_dir(old_dir)
    new = load_evidence_dir(new_dir)
    scenarios: list[dict[str, Any]] = []
    for scenario_id in sorted(set(old) | set(new)):
        if scenario_id in old and scenario_id in new:
            scenarios.append(compare_scenario(old[scenario_id], new[scenario_id]))
        else:
            scenarios.append({
                "scenario": scenario_id,
                "title": "", "dimension": "",
                "old_result": (old.get(scenario_id) or {}).get("result"),
                "new_result": (new.get(scenario_id) or {}).get("result"),
                "delta": "unpaired",
                "turns_changed": 0,
                "turns": [],
            })
    deltas: dict[str, int] = {}
    for entry in scenarios:
        deltas[entry["delta"]] = deltas.get(entry["delta"], 0) + 1
    return {
        "schema": "conversation-pairwise/v1",
        "old": _run_identity(old_dir),
        "new": _run_identity(new_dir),
        "totals": {"scenarios": len(scenarios), **deltas},
        "scenarios": scenarios,
    }


def _run_identity(directory: str | Path) -> dict[str, Any]:
    baseline = _load_envelope(Path(directory) / "baseline.json") or {}
    return {
        "evidence_dir": str(directory),
        "git_sha": baseline.get("git_sha", ""),
        "timestamp": baseline.get("timestamp", ""),
        "model": baseline.get("model", ""),
        "totals": baseline.get("totals", {}),
    }


def ratings_template(report: dict[str, Any]) -> list[dict[str, Any]]:
    """One human-rating row per scenario (Phase 36; all answers empty)."""
    rows: list[dict[str, Any]] = []
    for entry in report.get("scenarios", []):
        rows.append({
            "scenario": entry.get("scenario"),
            "title": entry.get("title"),
            "dimension": entry.get("dimension"),
            "delta": entry.get("delta"),
            "turns": [
                {"turn_index": t.get("turn_index"),
                 "user_text": t.get("user_text"),
                 "old_response": t.get("old_response"),
                 "new_response": t.get("new_response")}
                for t in entry.get("turns", [])
            ],
            "ratings": dict(RATING_QUESTIONS),
        })
    return rows


def collect_ratings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge human-filled rating rows into preference/score summary."""
    preferences: dict[str, int] = {}
    by_dimension: dict[str, dict[str, Any]] = {}
    score_sums: dict[str, float] = {}
    score_counts: dict[str, int] = {}
    answered = 0
    for row in rows:
        ratings = row.get("ratings") or {}
        if ratings.get("preference") not in ("old", "new", "tie"):
            continue
        answered += 1
        preferences[ratings["preference"]] = preferences.get(ratings["preference"], 0) + 1
        dim = str(row.get("dimension") or "unknown")
        cell = by_dimension.setdefault(
            dim, {"rows": 0, "prefer_new": 0, "prefer_old": 0, "tie": 0})
        cell["rows"] += 1
        cell[{"new": "prefer_new", "old": "prefer_old", "tie": "tie"}[ratings["preference"]]] += 1
        for key in _SCORE_KEYS:
            value = ratings.get(key)
            if isinstance(value, bool):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if 1.0 <= number <= 5.0:
                score_sums[key] = score_sums.get(key, 0.0) + number
                score_counts[key] = score_counts.get(key, 0) + 1
    return {
        "schema": "conversation-pairwise-ratings/v1",
        "answered": answered,
        "of": len(rows),
        "preferences": preferences,
        "mean_scores": {key: round(score_sums[key] / score_counts[key], 2)
                        for key in score_sums},
        "by_dimension": by_dimension,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pairwise old-vs-new conversation evaluation (plan 03 Phase 16)")
    sub = parser.add_subparsers(dest="command", required=True)
    compare = sub.add_parser("compare", help="diff two replay evidence dirs")
    compare.add_argument("--old", required=True, help="baseline evidence dir (previous Novi)")
    compare.add_argument("--new", required=True, help="candidate evidence dir (new Novi)")
    compare.add_argument("--out", required=True, help="output dir for pairwise.json + ratings template")
    collect = sub.add_parser("collect", help="merge filled human ratings")
    collect.add_argument("--in", dest="ratings_in", required=True,
                         help="ratings-template.jsonl with human answers filled in")
    collect.add_argument("--out", required=True, help="output path for ratings summary JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "compare":
        report = compare_runs(args.old, args.new)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "pairwise.json").write_text(json.dumps(report, indent=2))
        template = ratings_template(report)
        with (out / "ratings-template.jsonl").open("w") as handle:
            for row in template:
                handle.write(json.dumps(row) + "\n")
        totals = report["totals"]
        print(json.dumps(totals, indent=2))
        return 0
    if args.command == "collect":
        rows = [json.loads(line) for line in Path(args.ratings_in).read_text().splitlines()
                if line.strip()]
        summary = collect_ratings(rows)
        Path(args.out).write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        return 0
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
