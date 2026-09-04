"""Acceptance traces for conversational intelligence (plan 03, Sprint 1).

Plan 03 deliberately changes the validation philosophy: real end-to-end
behavior is the primary acceptance evidence, unit tests are regression
guards. This module is the instrumentation layer both rest on:

- ``FAILURE_LABELS`` — the Step 0.3 failure taxonomy (one response may
  carry several labels);
- ``AcceptanceTrace`` — one record per conversational turn covering the
  Phase 14.5 field set. Fields owned by later sprints (intent,
  referents, response goal, critic) are nullable and stay null until
  those sprints land — the schema is forward-compatible;
- ``InteractionRecord`` — the Step 0.2 complete interaction record used
  to build the real-conversation baseline corpus (JSONL, privacy-aware:
  raw input is recorded only when the caller permits it);
- ``evidence_envelope`` — the Phase 22 machine-readable evidence file
  format, plus the repo evidence-schema status values.

No behavior changes here: pure data + writers. Socket-free,
deterministic, stdlib-only.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Plan 03 Step 0.3 — every failure class the baseline classifier may assign.
FAILURE_LABELS = frozenset({
    "OUT_OF_CONTEXT",
    "WRONG_TOPIC",
    "WRONG_REFERENT",
    "INTENT_MISUNDERSTOOD",
    "DIALOGUE_ACT_WRONG",
    "MEMORY_MISSED",
    "MEMORY_IRRELEVANT",
    "MEMORY_HALLUCINATED",
    "WORLD_STATE_IGNORED",
    "PERCEPTION_IGNORED",
    "EMOTION_MISMATCH",
    "SOCIAL_MISMATCH",
    "TOO_GENERIC",
    "TOO_VERBOSE",
    "TOO_SHORT",
    "REPETITIVE",
    "UNNECESSARY_CLARIFICATION",
    "MISSING_CLARIFICATION",
    "CONTRADICTION",
    "HALLUCINATION",
    "FALSE_CAPABILITY",
    "BAD_TONE",
    "BAD_TIMING",
    "FAILURE_TO_LEARN",
    "FAILURE_TO_RECOVER",
    "MODEL_ROUTING_ERROR",
})

# Evidence-schema status values (docs/plans/EVIDENCE/01_EVIDENCE_SCHEMA.md).
STATUS_VALUES = frozenset({"PASS", "FAIL", "BLOCKED", "INCONCLUSIVE"})

SCHEMA_VERSION = "conversation-acceptance/v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_sha() -> str:
    """Best-effort repo revision for evidence provenance (never raises)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        sha = (out.stdout or "").strip()
        return sha if sha else "unknown"
    except Exception:
        return "unknown"


def check_labels(labels: list[str]) -> list[str]:
    unknown = [label for label in labels if label not in FAILURE_LABELS]
    if unknown:
        raise ValueError(f"unknown failure labels: {unknown}")
    return list(labels)


@dataclass
class AcceptanceTrace:
    """One scored conversational turn (plan 03 Phase 14.5 + Phase 22)."""

    scenario_id: str
    turn_index: int
    user_text: str
    response_text: str = ""
    reply_source: str = ""
    # Sprint 2+ fields: null until those sprints land.
    conversation_state: dict[str, Any] | None = None
    intent: dict[str, Any] | None = None
    referents: list[str] | None = None
    retrieved_context: dict[str, Any] = field(default_factory=dict)
    memory_used: list[str] = field(default_factory=list)
    world_used: dict[str, Any] = field(default_factory=dict)
    emotion_social: dict[str, Any] = field(default_factory=dict)
    response_goal: dict[str, Any] | None = None
    model_route: str = ""
    critic: dict[str, Any] | None = None
    repair_count: int = 0
    latency_ms: float = 0.0
    failure_labels: list[str] = field(default_factory=list)
    human_rating: float | None = None
    result: str = "INCONCLUSIVE"

    def __post_init__(self) -> None:
        check_labels(self.failure_labels)
        if self.result not in STATUS_VALUES:
            raise ValueError(f"unknown status: {self.result}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InteractionRecord:
    """Step 0.2 complete interaction record for the baseline corpus.

    ``raw_input`` is stored only when ``record_raw`` is true (privacy
    control for real-user collection); the replay harness always records
    it because scenario text is not personal data.
    """

    conversation_id: str
    turn_id: int
    timestamp: str
    modality: str
    raw_input: str = ""
    normalized_input: str = ""
    conversation_state: dict[str, Any] = field(default_factory=dict)
    retrieved_memories: list[str] = field(default_factory=list)
    retrieved_world: dict[str, Any] = field(default_factory=dict)
    identity_context: dict[str, Any] = field(default_factory=dict)
    social_emotional: dict[str, Any] = field(default_factory=dict)
    intent: dict[str, Any] | None = None
    referents: list[str] = field(default_factory=list)
    response_strategy: str = ""
    model: str = ""
    model_config: dict[str, Any] = field(default_factory=dict)
    response: str = ""
    reply_source: str = ""
    response_verification: dict[str, Any] = field(default_factory=dict)
    memory_updates: list[str] = field(default_factory=list)
    user_correction: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def append_interaction_record(path: str | Path, record: InteractionRecord) -> None:
    """Append one JSONL record (creates parent dirs; never raises)."""
    try:
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=True) + "\n")
    except Exception:
        pass


def evidence_envelope(
    *,
    scenario_id: str,
    title: str,
    dimension: str,
    model: str,
    runtime: str,
    configuration: dict[str, Any],
    turns: list[AcceptanceTrace],
    result: str,
    failure_labels: list[str] | None = None,
    human_rating: float | None = None,
) -> dict[str, Any]:
    """Phase 22 evidence artifact for one scenario run."""
    if result not in STATUS_VALUES:
        raise ValueError(f"unknown status: {result}")
    labels = check_labels(list(failure_labels or []))
    last = turns[-1].to_dict() if turns else {}
    return {
        "schema": SCHEMA_VERSION,
        "scenario": scenario_id,
        "title": title,
        "dimension": dimension,
        "git_sha": git_sha(),
        "timestamp": utc_now_iso(),
        "runtime": runtime,
        "model": model,
        "configuration": dict(configuration),
        "conversation": [t.to_dict() for t in turns],
        "state_before": (turns[0].to_dict().get("conversation_state")
                         if turns else None),
        "intent": last.get("intent"),
        "referents": last.get("referents"),
        "context": last.get("retrieved_context"),
        "memory": last.get("memory_used"),
        "world": last.get("world_used"),
        "response_plan": last.get("response_goal"),
        "response": last.get("response_text"),
        "critic": last.get("critic"),
        "latency_ms": last.get("latency_ms"),
        "result": result,
        "failure_labels": labels,
        "human_rating": human_rating,
    }


def write_evidence(path: str | Path, envelope: dict[str, Any]) -> Path:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(envelope, indent=2, ensure_ascii=True), encoding="utf-8")
    return dest
