"""Active grounding: escalation policy, budgets, dedup, short-term cache
(plan Phase 6, Steps 6.1/6.3/6.4/6.5).

Division of labor (analysis doc 04 §6/§7):
- cognition owns the semantic query text (e.g. "small keyring on the desk");
- perception owns WHEN to spend expensive grounding compute and with WHAT
  budget — this module is that perception-side half.

Escalation rules (Step 6.1), implemented by `GroundingEscalationPolicy`:
- SSDLite confidence low            -> grounding request
- category known, description ambiguous -> grounding request
- planner/cognition asks directly   -> pass-through request
- prediction violated               -> re-ground the whole scene
- memory expects object, not seen   -> active search query

Every request carries a `GroundingBudget` (Step 6.3): time budget, compute
units, max retries, max frames, risk class. `GroundingRequestDeduplicator`
(Step 6.4) prevents re-spending inference on the same (frame, query) pair.
`GroundingCache` (Step 6.5) is short-lived only — nothing here promotes to
durable memory; Novi's normal memory policy owns that.

Pure stdlib; deterministic; no brain imports (cognition calls this seam).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import OrderedDict

from novi.perception.grounding import GroundingResult, SpatialInferenceMode

_REGROUND_SCENE = "locate all objects visible in the image"


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


@dataclass(frozen=True)
class GroundingBudget:
    """Bounded resources for one active-perception request (plan Step 6.3)."""

    time_budget_ms: int = 5000
    compute_budget_units: int = 1  # one grounding call == one unit
    max_retries: int = 1
    max_frames: int = 1
    risk_class: str = "routine"

    def __post_init__(self) -> None:
        for name, value in (
            ("time_budget_ms", self.time_budget_ms),
            ("compute_budget_units", self.compute_budget_units),
            ("max_retries", self.max_retries),
            ("max_frames", self.max_frames),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive, got {value}")
        if not self.risk_class:
            raise ValueError("risk_class must be non-empty")


@dataclass(frozen=True)
class GroundingRequest:
    """One budgeted request to execute a semantic query against one frame."""

    query: str
    frame_id: str
    reason: str
    budget: GroundingBudget = field(default_factory=GroundingBudget)
    requester: str = "active_perception"
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query must be non-empty")
        if not self.frame_id:
            raise ValueError("frame_id must be non-empty")
        if not self.reason:
            raise ValueError("reason must be non-empty")


@dataclass(frozen=True)
class EscalationSignal:
    """Per-frame context cognition/perception feeds into the policy."""

    frame_id: str
    low_confidence_labels: tuple[str, ...] = ()
    expected_labels: tuple[str, ...] = ()
    ambiguous_labels: tuple[str, ...] = ()
    planner_queries: tuple[str, ...] = ()
    prediction_violated: bool = False


class GroundingEscalationPolicy:
    """Decision rules: when does a frame escalate to expensive grounding?

    Pure function of the signal; produces deduped, capped, budgeted requests.
    The confidence floor is a policy input (default 0.70) — the same spirit
    as DeterministicObjectDetector's floor, applied to SSDLite output.
    """

    def __init__(
        self,
        *,
        max_requests_per_signal: int = 4,
        budget_factory=None,
    ) -> None:
        self._cap = max_requests_per_signal
        self._budget_factory = budget_factory or (lambda: GroundingBudget())

    def evaluate(self, signal: EscalationSignal) -> tuple[GroundingRequest, ...]:
        requests: list[GroundingRequest] = []
        seen: set[str] = set()

        def add(query: str, reason: str, requester: str = "active_perception") -> None:
            key = _norm(query)
            if key in seen or len(requests) >= self._cap:
                return
            seen.add(key)
            requests.append(
                GroundingRequest(
                    query=query,
                    frame_id=signal.frame_id,
                    reason=reason,
                    budget=self._budget_factory(),
                    requester=requester,
                )
            )

        for query in signal.planner_queries:
            add(query, "planner_request", requester="planner")
        for label in signal.low_confidence_labels:
            add(f"locate the {label}", "ssdlite_low_confidence")
        for label in signal.ambiguous_labels:
            add(f"locate the {label}", "ambiguous_description")
        if signal.prediction_violated:
            add(_REGROUND_SCENE, "prediction_violated")
        for label in signal.expected_labels:
            add(f"find the {label}", "expected_but_missing")
        return tuple(requests)


class GroundingRequestDeduplicator:
    """Short-lived (frame_id, query) memory (plan Step 6.4).

    Prevents re-spending inference on the exact same pair unless policy
    explicitly asks for a repeat (caller can bypass by not asking).
    """

    def __init__(self, *, max_entries: int = 128) -> None:
        self._seen: OrderedDict[tuple[str, str], None] = OrderedDict()
        self._max = max_entries

    def is_duplicate(self, frame_id: str, query: str) -> bool:
        return (frame_id, _norm(query)) in self._seen

    def remember(self, frame_id: str, query: str) -> None:
        key = (frame_id, _norm(query))
        self._seen[key] = None
        self._seen.move_to_end(key)
        while len(self._seen) > self._max:
            self._seen.popitem(last=False)


class GroundingCache:
    """Short-lived query/frame result cache (plan Step 6.5).

    Explicitly NOT durable memory: entries are LRU-evicted in-process and
    die with the process. Promotion to Novi memory is the memory policy's
    job, never this cache's.
    """

    def __init__(self, *, maxsize: int = 32) -> None:
        self._cache: OrderedDict[tuple[str, str, str], GroundingResult] = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _key(frame_id: str, query: str, mode: SpatialInferenceMode) -> tuple[str, str, str]:
        return (frame_id, _norm(query), mode.value)

    def get(self, frame_id: str, query: str, mode: SpatialInferenceMode) -> GroundingResult | None:
        key = self._key(frame_id, query, mode)
        result = self._cache.get(key)
        if result is None:
            self._misses += 1
            return None
        self._hits += 1
        self._cache.move_to_end(key)
        return result

    def put(self, result: GroundingResult) -> None:
        key = self._key(result.frame_id, result.query, result.inference_mode)
        self._cache[key] = result
        self._cache.move_to_end(key)
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}
