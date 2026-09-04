"""Failure-dataset exporter (plan 03 Phase 11.1/11.2 — data prep only).

Builds contrastive SFT-ready pairs from FAIL scenario evidence: the bad
response, the failure labels, the packet snapshot that produced it, and a
heuristic ideal-behavior skeleton. No training happens here; the output
JSONL is the input to the future SFT/DPO stage (Sprint 8), which needs a
human + GPU-gated run.

Ideal skeletons are marked ``source: heuristic-v1`` — a human reviewer
promotes them to gold (Step 0.4) before any training use. Never present
heuristic skeletons as reviewed ground truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "conversation-sft-seed/v1"


def _ideal_skeleton(*, labels: list[str], packet: dict[str, Any]) -> dict[str, Any]:
    memories = packet.get("relevant_memories") or []
    memory_contents = [str(m.get("content", "")) for m in memories
                       if isinstance(m, dict) and m.get("content")]
    if "MEMORY_MISSED" in labels and memory_contents:
        return {"source": "heuristic-v1",
                "should_have_recalled": memory_contents[:2]}
    if "WRONG_REFERENT" in labels:
        resolved = packet.get("resolved_entities") or {}
        return {"source": "heuristic-v1",
                "should_have_resolved": resolved}
    if "UNNECESSARY_CLARIFICATION" in labels:
        return {"source": "heuristic-v1",
                "should_have_answered_directly": True}
    if "MISSING_CLARIFICATION" in labels:
        return {"source": "heuristic-v1",
                "should_have_asked": True}
    return {"source": "heuristic-v1", "note": "reviewer must supply ideal"}


def export_failure_dataset(evidence_dir: str | Path,
                           out_path: str | Path) -> dict[str, Any]:
    """Export contrastive pairs from FAIL evidence. Returns a summary."""
    evidence_dir = Path(evidence_dir)
    pairs: list[dict[str, Any]] = []
    scenarios_seen = 0
    for path in sorted((evidence_dir / "scenarios").glob("*.json")):
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        scenarios_seen += 1
        if envelope.get("result") != "FAIL":
            continue
        for turn in envelope.get("conversation") or []:
            labels = turn.get("failure_labels") or []
            if not labels:
                continue
            packet = ((turn.get("retrieved_context") or {}).get("grounding")
                      or {}).get("packet") or {}
            pairs.append({
                "schema": SCHEMA,
                "scenario": envelope.get("scenario"),
                "turn_index": turn.get("turn_index"),
                "user_text": turn.get("user_text"),
                "bad_response": turn.get("response_text"),
                "failure_labels": labels,
                "packet_snapshot": {
                    "intent": ((turn.get("retrieved_context") or {})
                               .get("trace") or {}).get("conversation",
                                                        {}).get("intent"),
                    "relevant_memories": packet.get("relevant_memories", []),
                    "resolved_entities": packet.get("resolved_entities", {}),
                },
                "ideal_skeleton": _ideal_skeleton(labels=labels,
                                                  packet=packet),
                "provenance": {
                    "git_sha": envelope.get("git_sha"),
                    "model": envelope.get("model"),
                    "scenario_file": path.name,
                },
            })
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for pair in pairs:
            fh.write(json.dumps(pair, ensure_ascii=True) + "\n")
    by_label: dict[str, int] = {}
    for pair in pairs:
        for label in pair["failure_labels"]:
            by_label[label] = by_label.get(label, 0) + 1
    return {"scenarios_seen": scenarios_seen, "pairs": len(pairs),
            "by_label": dict(sorted(by_label.items(), key=lambda kv: -kv[1])),
            "out": str(out_path)}
