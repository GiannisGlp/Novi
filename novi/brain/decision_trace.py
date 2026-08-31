"""End-to-end decision traces (plan 22, Phase 23).

Every meaningful interaction produces a trace: trace_id, cycle_id, time,
input/event, perception evidence, world changes, identity resolution,
retrieved memories, attention scores, prediction, cognitive hypotheses,
goals, social context, dialogue candidates, selected decision, initiative
score, LLM model, LLM latency, response, outcome, memory writes.

Required to debug why Novi said something (plan §27); bounded, never
unbounded growth.
"""

from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

MAX_TRACES = 64


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DecisionTrace:
    trace_id: str
    cycle_id: int
    time: str
    input_event: str = ""
    perception_evidence: list[str] = field(default_factory=list)
    world_changes: list[str] = field(default_factory=list)
    identity_resolution: dict[str, Any] = field(default_factory=dict)
    retrieved_memories: list[str] = field(default_factory=list)
    attention_scores: list[dict[str, Any]] = field(default_factory=list)
    prediction: str = ""
    hypotheses: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    social_context: dict[str, Any] = field(default_factory=dict)
    dialogue_act: str = ""
    dialogue_reason: str = ""
    initiative_score: float = 0.0
    llm_model: str = ""
    llm_latency_s: float = 0.0
    response: str = ""
    outcome: str = ""
    memory_writes: list[str] = field(default_factory=list)
    # plan 24 §29: emotional outcome record — the user's reaction and any
    # correction, plus the realized style and failure bookkeeping.
    user_reaction: str = ""
    correction: str = ""
    verbosity: str = "short"
    defensiveness: str = "none"
    novi_caused_problem: bool = False
    repeat_count: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "cycle_id": self.cycle_id,
            "time": self.time,
            "input_event": self.input_event,
            "perception_evidence": list(self.perception_evidence),
            "world_changes": list(self.world_changes),
            "identity_resolution": dict(self.identity_resolution),
            "retrieved_memories": list(self.retrieved_memories),
            "attention_scores": list(self.attention_scores),
            "prediction": self.prediction,
            "hypotheses": list(self.hypotheses),
            "goals": list(self.goals),
            "social_context": dict(self.social_context),
            "dialogue_act": self.dialogue_act,
            "dialogue_reason": self.dialogue_reason,
            "initiative_score": round(self.initiative_score, 3),
            "llm_model": self.llm_model,
            "llm_latency_s": round(self.llm_latency_s, 3),
            "response": self.response,
            "outcome": self.outcome,
            "memory_writes": list(self.memory_writes),
            "user_reaction": self.user_reaction,
            "correction": self.correction,
            "verbosity": self.verbosity,
            "defensiveness": self.defensiveness,
            "novi_caused_problem": self.novi_caused_problem,
            "repeat_count": self.repeat_count,
        }


class TraceRecorder:
    """Bounded ring of decision traces."""

    def __init__(self, *, max_traces: int = MAX_TRACES) -> None:
        self.max_traces = max_traces
        self._traces: deque[DecisionTrace] = deque(maxlen=max_traces)

    def new_trace(self, *, cycle_id: int, input_event: str = "") -> DecisionTrace:
        trace = DecisionTrace(
            trace_id=f"trace-{uuid.uuid4().hex[:10]}",
            cycle_id=cycle_id,
            time=utc_now_iso(),
            input_event=input_event,
        )
        self._traces.append(trace)
        return trace

    def latest(self) -> DecisionTrace | None:
        return self._traces[-1] if self._traces else None

    def find(self, trace_id: str) -> DecisionTrace | None:
        for t in self._traces:
            if t.trace_id == trace_id:
                return t
        return None

    def snapshot(self, limit: int = 8) -> list[dict[str, Any]]:
        return [t.snapshot() for t in list(self._traces)[-limit:]]
