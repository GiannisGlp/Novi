"""Failure-driven training data (plan 03 Phases 11, 25, 26; Sprint 8 prep).

Training is driven by real failures, never arbitrary volume — and NEVER
by unreviewed heuristic text. Two outputs:

1. ``candidates`` — contrastive rows built from FAIL scenario evidence:
   the full packet situation, the planned act, the bad response, and a
   heuristic ideal hint (``needs_review: true``). These are REVIEW
   QUEUE entries, not training data. A human promotes the hint to a
   gold ideal (plan Step 0.4) before any training use.
2. ``gold`` — train-ready SFT + DPO rows built ONLY from human-graded
   sessions (conversation_grade evidence) where the reviewer supplied
   ``what_instead``. No human ideal, no gold row. An empty gold file
   with a clean benchmark is the CORRECT output, not a failure.

Row shapes match the training backends (``situation`` + ``decision``
-> ``preferred_response`` for SFT; ``response_a``/``response_b`` +
``preferred`` for DPO). The manifest records the source evidence
git SHAs and the frozen benchmark reference so model promotion stays
evidence-based (plan §25/§28: evaluate against the frozen benchmark
before promotion; DPO only when SFT + orchestration leave systematic
preference failures).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def packet_to_situation(packet: dict[str, Any]) -> dict[str, Any]:
    """Shrink a packet snapshot to the SFT ``situation`` contract."""
    anchor = packet.get("anchor") or {}
    memories = []
    for mem in packet.get("relevant_memories") or []:
        if not isinstance(mem, dict):
            continue
        memories.append({
            "summary": str(mem.get("content", ""))[:300],
            "confidence": mem.get("confidence", 0.0),
            "source": str(mem.get("source", "")),
        })
    world = []
    for fact in packet.get("world_context") or []:
        if isinstance(fact, dict):
            world.append(str(fact.get("text", ""))[:200])
        elif fact:
            world.append(str(fact)[:200])
    return {
        "person": {"id": str((packet.get("identity_context") or {}).get("addressee", "") or "user")},
        "world": {"observations": world[:5]},
        "conversation": {
            "topic": str(anchor.get("topic", "") or ""),
            "input": str(packet.get("current_turn", ""))[:300],
            "entities": list((packet.get("resolved_entities") or {}).values())[:4],
            "uncertainty": list(packet.get("uncertainty") or [])[:3],
        },
        "memory": memories[:5],
        "social": dict(packet.get("social_context") or {}),
    }


def build_candidates(evidence_dir: str | Path) -> list[dict[str, Any]]:
    """Contrastive review-queue rows from FAIL scenario evidence."""
    from novi.brain.conversation_dataset import _ideal_skeleton

    evidence_dir = Path(evidence_dir)
    rows: list[dict[str, Any]] = []
    for path in sorted((evidence_dir / "scenarios").glob("*.json")):
        try:
            envelope = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(envelope, dict) or envelope.get("result") != "FAIL":
            continue
        for turn in envelope.get("conversation") or []:
            if not isinstance(turn, dict) or turn.get("result") != "FAIL":
                continue
            context = turn.get("retrieved_context") or {}
            trace = (context.get("trace") or {}).get("conversation", {}) or {}
            packet = (context.get("grounding") or {}).get("packet", {}) or {}
            goal = trace.get("response_goal") or {}
            labels = list(turn.get("failure_labels") or [])
            hint = _ideal_skeleton(labels=labels, packet=packet)
            rows.append({
                "example_id": f"cand-{envelope.get('scenario')}-t{turn.get('turn_index', 0)}",
                "task": "contextual_response",
                "situation": packet_to_situation(packet),
                "decision": {
                    "dialogue_act": str(goal.get("goal", "") or ""),
                    "reason": str(goal.get("reason", "") or ""),
                },
                "bad_response": str(turn.get("response_text") or ""),
                "failure_labels": labels,
                "ideal_hint": hint,
                "needs_review": True,
                "synthetic": True,
            })
    return rows


def build_gold(graded_session: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Train-ready SFT + DPO rows from human-graded sessions.

    Only turns graded MAJOR ISSUE/FAIL *with* a reviewer-supplied
    ``what_instead`` qualify. Everything else is skipped silently.
    """
    sft: list[dict[str, Any]] = []
    dpo: list[dict[str, Any]] = []
    for turn in graded_session.get("graded_turns") or []:
        if not isinstance(turn, dict):
            continue
        if turn.get("grade") not in ("MAJOR ISSUE", "FAIL"):
            continue
        ideal = str(turn.get("what_instead") or "").strip()
        bad = str(turn.get("response") or "").strip()
        if not ideal or not bad:
            continue
        intent = turn.get("intent") or {}
        situation = {
            "person": {"id": "user"},
            "world": {"observations": []},
            "conversation": {"input": str(turn.get("user_text") or "")[:300]},
            "memory": [],
            "social": {},
        }
        decision = {"dialogue_act": "ANSWER_DIRECTLY",
                    "reason": f"reviewer correction; intent={intent.get('intent', '') if isinstance(intent, dict) else ''}"}
        example_id = f"gold-{turn.get('conversation_id')}-t{turn.get('turn_id')}"
        sft.append({
            "example_id": example_id,
            "task": "contextual_response",
            "situation": situation,
            "decision": decision,
            "preferred_response": ideal,
            "synthetic": False,
            "reviewed": True,
        })
        dpo.append({
            "example_id": example_id,
            "task": "contextual_response",
            "situation": situation,
            "decision": decision,
            "response_a": bad,
            "response_b": ideal,
            "preferred": "b",
            "synthetic": False,
            "reviewed": True,
        })
    return sft, dpo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Failure-driven training data builders (plan 03 Sprint 8 prep)")
    sub = parser.add_subparsers(dest="command", required=True)
    candidates = sub.add_parser("candidates", help="review queue from FAIL evidence")
    candidates.add_argument("--evidence-dir", required=True)
    candidates.add_argument("--out", required=True)
    gold = sub.add_parser("gold", help="train-ready rows from a graded session")
    gold.add_argument("--graded-session", required=True)
    gold.add_argument("--out-sft", required=True)
    gold.add_argument("--out-dpo", required=True)
    gold.add_argument("--out-manifest", default="")
    return parser


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "candidates":
        rows = build_candidates(args.evidence_dir)
        _write_jsonl(Path(args.out), rows)
        print(json.dumps({"candidates": len(rows)}))
        return 0
    if args.command == "gold":
        session = json.loads(Path(args.graded_session).read_text())
        sft, dpo = build_gold(session)
        _write_jsonl(Path(args.out_sft), sft)
        _write_jsonl(Path(args.out_dpo), dpo)
        if args.out_manifest:
            Path(args.out_manifest).write_text(json.dumps({
                "schema": "conversation-training-manifest/v1",
                "sft_rows": len(sft),
                "dpo_rows": len(dpo),
                "promotion_rule": ("promote only after the candidate beats "
                                   "the frozen benchmark; DPO only for "
                                   "systematic preference failures SFT does "
                                   "not solve (plan §25-26)"),
            }, indent=2))
        print(json.dumps({"sft": len(sft), "dpo": len(dpo)}))
        return 0
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
