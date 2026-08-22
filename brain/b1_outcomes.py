"""Stage-0 simulation scaffold — LEGACY (not imported by MAC_BRAIN; retained only for the brain/tests suite).

Do not extend these types for the brain phase — new work targets MAC_BRAIN/.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .b1_autonomy import ActionProposal


@dataclass(frozen=True)

class ActionOutcome:
    proposal_id: str
    status: str
    observed_effects: tuple[str, ...]
    discrepancies: tuple[str, ...]
    replayable: bool = True


class DeterministicOutcomeEvaluator:
    """B1.6 outcome evaluator: classify simulated results without execution."""

    def evaluate(
        self,
        proposal: ActionProposal,
        *,
        observed_effects: Iterable[str],
        expected_effects: Iterable[str] | None = None,
    ) -> ActionOutcome:
        observed = tuple(observed_effects)
        expected = tuple(expected_effects or ())
        discrepancies = tuple(effect for effect in expected if effect not in observed)
        status = "SUCCEEDED" if not discrepancies else "DIVERGED"
        return ActionOutcome(
            proposal_id=proposal.proposal_id,
            status=status,
            observed_effects=observed,
            discrepancies=discrepancies,
        )


@dataclass(frozen=True)
class ReplayRecord:
    cycle: int
    proposal_id: str
    outcome_status: str


class DeterministicReplay:
    """Minimal append-only replay ledger for deterministic B1 validation."""

    def __init__(self) -> None:
        self._records: list[ReplayRecord] = []

    def record(self, cycle: int, outcome: ActionOutcome) -> None:
        self._records.append(ReplayRecord(cycle, outcome.proposal_id, outcome.status))

    def replay(self) -> tuple[ReplayRecord, ...]:
        return tuple(self._records)

    @property
    def count(self) -> int:
        return len(self._records)
