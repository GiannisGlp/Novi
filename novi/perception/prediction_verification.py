"""Prediction verification via grounding (plan Step 21).

The brain's prediction engine predicts objects will appear
(PredictionEngine.observe(present, cycle)); grounding verifies those
expectations. Rules:

- a successful grounding result with a matching observation  -> present;
- a successful result without one                          -> absent;
- a FAILED result                                          -> UNKNOWN (None),
  fail-closed: absence is never inferred from a failure (plan Step 9.4).

`as_present_set()` feeds directly into PredictionEngine.observe(present, cycle).
Pure stdlib, deterministic, protocol-free (works on any GroundingResult).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from novi.perception.grounding import GroundingObservation, GroundingResult, PointObservation

LabelMatcher = Callable[[GroundingObservation | PointObservation, str], bool]


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _default_match(obs: GroundingObservation | PointObservation, label: str) -> bool:
    a, b = _norm(obs.label), _norm(label)
    return a == b or a in b or b in a


@dataclass(frozen=True)
class PresenceVerdict:
    label: str
    present: bool | None  # None == unknown (backend failed); never infer absence
    matched_observation_id: str | None = None


@dataclass(frozen=True)
class PredictionVerification:
    verdicts: tuple[PresenceVerdict, ...]

    @property
    def all_known(self) -> bool:
        return all(v.present is not None for v in self.verdicts)

    def as_present_set(self) -> set[str]:
        """Verified-present labels — the `present` arg for the prediction engine."""
        return {v.label for v in self.verdicts if v.present}


def verify_predicted_presence(
    result: GroundingResult,
    expected_labels: tuple[str, ...],
    *,
    match: LabelMatcher | None = None,
) -> PredictionVerification:
    matcher = match or _default_match
    verdicts: list[PresenceVerdict] = []
    for label in expected_labels:
        if not result.success:
            verdicts.append(PresenceVerdict(label=label, present=None))
            continue
        matched_id: str | None = None
        for obs in result.observations:
            if matcher(obs, label):
                matched_id = obs.observation_id
                break
        verdicts.append(PresenceVerdict(label=label, present=matched_id is not None, matched_observation_id=matched_id))
    return PredictionVerification(verdicts=tuple(verdicts))
