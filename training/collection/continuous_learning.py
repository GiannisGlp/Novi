"""Continuous emotional learning cycle (plan 24 §46, §51 item 37).

The §46 loop:

    interaction -> ... -> outcome -> interaction memory -> quality filtering
    -> training example -> SFT/DPO/policy ranking -> evaluation -> shadow
    deployment -> approved model -> new interaction

This module is the cycle coordinator. It accumulates quality-filtered
preference signals into a growing log and, when enough have accumulated,
*plans* a training cycle. It never trains or deploys itself — "never
automatically train/deploy directly from raw emotional observations"
(plan §46). A human/operator executes the plan and calls `complete_cycle`
with the outcome.

    outcome/feedback records -> quality_filter -> accumulate_cycle -> log
    state.signals_since_cycle -> should_train -> plan_cycle -> (operator)
    -> complete_cycle -> new accumulation period
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from training.collection.preference_learning import accumulate_preferences

# Default minimum quality-filtered signals before a training cycle is planned.
DEFAULT_MIN_SIGNALS = 50

# plan §29: only explicit positive reactions confirm success. Silence alone
# (a bare "acknowledged" outcome) is never treated as a learning signal.
_EXPLICIT_POSITIVE = frozenset({"thanks", "follow_up"})


@dataclass
class CycleState:
    """Accumulation state for the continuous learning loop."""

    signals_since_cycle: int = 0
    cycles_run: int = 0
    last_cycle_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "signals_since_cycle": self.signals_since_cycle,
            "cycles_run": self.cycles_run,
            "last_cycle_at": self.last_cycle_at,
        }


@dataclass(frozen=True)
class CycleReport:
    """A planned (not executed) training cycle (plan §46 'training example')."""

    signals: int
    training_kind: str
    adapter_dir: str
    config: str
    dataset: str
    ready: bool
    planned_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signals": self.signals,
            "training_kind": self.training_kind,
            "adapter_dir": self.adapter_dir,
            "config": self.config,
            "dataset": self.dataset,
            "ready": self.ready,
            "planned_at": self.planned_at,
        }


@dataclass(frozen=True)
class CycleCompletion:
    """The outcome of a finished cycle (plan §46 'approved model')."""

    accepted: bool
    signals_consumed: int
    cycles_run: int
    completed_at: str


def quality_filter(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only records with an explicit learning signal (plan §46 quality filtering).

    Raw emotional observations are never training candidates: a record is
    kept only when it carries explicit feedback, a correction, or an explicit
    positive reaction. Silence alone is never a signal (plan §29).
    """
    out: list[dict[str, Any]] = []
    for rec in records:
        if "kind" in rec:
            out.append(rec)
            continue
        outcome = rec.get("outcome", "")
        reaction = rec.get("user_reaction", "")
        if (outcome == "corrected" or reaction == "correction"
                or reaction in _EXPLICIT_POSITIVE):
            out.append(rec)
    return out


def _existing_signal_count(log_path: str | Path) -> int:
    p = Path(log_path)
    if not p.exists():
        return 0
    return sum(1 for line in p.read_text().splitlines() if line.strip())


def accumulate_cycle(records: list[dict[str, Any]], state: CycleState,
                     log_path: str | Path) -> list[dict[str, Any]]:
    """Quality-filter records and append their preference signals to the log.

    Signals are renumbered to continue the existing log so ids stay
    sequential and appendable. Returns the new signals (with final ids).
    """
    filtered = quality_filter(records)
    signals = accumulate_preferences(filtered)
    if not signals:
        return []
    offset = _existing_signal_count(log_path)
    for i, sig in enumerate(signals):
        sig["example_id"] = f"emo-pref-lt-{offset + i + 1:04d}"
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        for sig in signals:
            f.write(json.dumps(sig, ensure_ascii=False) + "\n")
    state.signals_since_cycle += len(signals)
    return signals


def should_train(state: CycleState, min_signals: int = DEFAULT_MIN_SIGNALS) -> bool:
    """True when enough quality-filtered signals have accumulated to train."""
    return state.signals_since_cycle >= min_signals


def plan_cycle(state: CycleState, *, adapter_dir: str, training_kind: str,
               config: str, dataset: str,
               min_signals: int = DEFAULT_MIN_SIGNALS) -> CycleReport:
    """Plan (not execute) a training cycle from the accumulated signals."""
    return CycleReport(
        signals=state.signals_since_cycle,
        training_kind=training_kind,
        adapter_dir=adapter_dir,
        config=config,
        dataset=dataset,
        ready=should_train(state, min_signals),
        planned_at=_now(),
    )


def complete_cycle(state: CycleState, *, accepted: bool,
                   at: str | None = None) -> CycleCompletion:
    """Record a finished cycle: reset accumulation, bump the cycle counter.

    Whether the cycle's model was accepted or rejected, the accumulated
    signals were consumed by the training run, so a new accumulation period
    begins.
    """
    completion = CycleCompletion(
        accepted=accepted,
        signals_consumed=state.signals_since_cycle,
        cycles_run=state.cycles_run + 1,
        completed_at=at or _now(),
    )
    state.signals_since_cycle = 0
    state.cycles_run += 1
    state.last_cycle_at = completion.completed_at
    return completion


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
