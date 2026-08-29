"""Active perception for the Mac Brain (06_AUTONOMY doc 04).

Turns perception from a passive stream into a capability Novi deliberately
invokes when additional information can improve a decision:

  Goal / uncertainty → information need → PerceptionQuery →
  SSDLite / LocateAnything / future sensors → observation validation →
  world-state update → decision improvement

Design rules enforced here (doc 04 + the LocateAnything implementation plan):

- **SSDLite stays the continuous, low-cost detector.** Expensive grounding is
  invoked only when the arbitration predicates say it can change a decision.
- **Raw model output never enters the world model.** ``StrictBoxParser``
  rejects malformed/inverted/out-of-range boxes; typed observations carry
  model/version provenance.
- **Search is bounded.** ``ActiveSearch`` stops after budget exhaustion and
  reports not-found uncertainty — it never hallucinates success (A-PERCEPT-01).
- **Escalation is monotonic and stoppable**: fast detector → tracking →
  targeted VLM → viewpoint change → human clarification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

# ---------------------------------------------------------------------------
# PerceptionQuery (doc 04 Step 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerceptionQuery:
    query_id: str
    natural_language: str
    structured_target: str = ""                # canonical entity/class name if known
    sensor_requirements: tuple[str, ...] = ("ssdlite",)
    spatial_scope: str = ""                    # region / frame / viewpoint
    max_latency_s: float = 10.0
    confidence_threshold: float = 0.5
    information_value: float = 0.0
    privacy_level: str = "unclassified"
    requester_goal_id: str = ""

    @classmethod
    def for_goal(cls, target: str, *, goal_id: str, confidence_threshold: float = 0.5) -> "PerceptionQuery":
        return cls(
            query_id=f"pq-{uuid4().hex[:10]}",
            natural_language=f"where is {target}?",
            structured_target=target,
            requester_goal_id=goal_id,
            confidence_threshold=confidence_threshold,
        )


# ---------------------------------------------------------------------------
# Typed observations and the LocateAnything-style backend boundary (Step 3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DetectionBox:
    """A validated 2D box in normalized image coordinates (0..1)."""
    label: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    source: str = "backend"
    model_version: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "label": self.label, "confidence": round(self.confidence, 4),
            "box": [round(self.x1, 4), round(self.y1, 4), round(self.x2, 4), round(self.y2, 4)],
            "source": self.source, "model_version": self.model_version,
        }


@dataclass(frozen=True)
class LocateResult:
    query_id: str
    found: bool
    # Typed backends emit DetectionBox; raw adapters emit dicts that must pass
    # StrictBoxParser before anything enters the world model (doc 04 Step 3).
    boxes: tuple[DetectionBox | dict[str, Any], ...]
    latency_s: float
    model_version: str
    failure_reason: str = ""          # model_unavailable | timeout | malformed_output | ...
    not_found_reason: str = ""        # no_match | budget_exhausted | ambiguous | ...

    @property
    def best(self) -> DetectionBox | None:
        typed = [b for b in self.boxes if isinstance(b, DetectionBox)]
        return max(typed, key=lambda b: b.confidence) if typed else None


class LocateBackend(Protocol):
    """Novi-owned interface for an optional grounding model (e.g. LocateAnything).

    Must accept an image + query, return typed observations with provenance,
    and expose latency + failure reason. Replaceable; never a core dependency.
    """

    def locate(self, image: Any, query: PerceptionQuery, *, cycle: int) -> LocateResult: ...


class StrictBoxParser:
    """Parses a grounding model's coordinate output strictly (doc 04 Step 3).

    Accepts dicts of the form {"label": str, "confidence": float,
    "box": [x1, y1, x2, y2]} with normalized 0..1 coordinates. Rejects:
    malformed shapes, inverted boxes (x2 <= x1 / y2 <= y1), out-of-range
    coordinates, and NaN/inf values.
    """

    def parse(self, raw: Any, *, source: str = "backend", model_version: str = "") -> tuple[DetectionBox | None, str]:
        if not isinstance(raw, dict):
            return None, "malformed_output: not a dict"
        label = raw.get("label")
        if not isinstance(label, str) or not label:
            return None, "malformed_output: missing label"
        confidence = raw.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            return None, "malformed_output: invalid confidence"
        box = raw.get("box")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            return None, "malformed_output: box must have 4 values"
        try:
            x1, y1, x2, y2 = (float(v) for v in box)
        except (TypeError, ValueError):
            return None, "malformed_output: non-numeric box"
        for v in (x1, y1, x2, y2):
            if v != v or v in (float("inf"), float("-inf")):  # NaN / inf
                return None, "malformed_output: non-finite coordinate"
        if not all(0.0 <= v <= 1.0 for v in (x1, y1, x2, y2)):
            return None, "out_of_range: coordinates must be normalized 0..1"
        if x2 <= x1 or y2 <= y1:
            return None, "inverted_box: x2/x1 or y2/y1 inverted"
        return DetectionBox(label=label, confidence=float(confidence), x1=x1, y1=y1, x2=x2, y2=y2,
                            source=source, model_version=model_version), ""


# ---------------------------------------------------------------------------
# Query arbitration (doc 04 Step 4)
# ---------------------------------------------------------------------------


class QueryArbitrator:
    """Only invoke expensive grounding when it can change a decision."""

    def should_query(
        self,
        *,
        user_asked_specific: bool = False,
        ssdlite_ambiguous: bool = False,
        identity_uncertain: bool = False,
        prediction_error: bool = False,
        plan_needs_fact: bool = False,
        freshness_insufficient: bool = False,
    ) -> bool:
        return any([
            user_asked_specific,
            ssdlite_ambiguous,
            identity_uncertain,
            prediction_error,
            plan_needs_fact,
            freshness_insufficient,
        ])


# ---------------------------------------------------------------------------
# Budgets and information-gain scoring (docs 04 Steps 7 & 9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerceptionBudget:
    max_vlm_queries: int = 3
    max_camera_search_cycles: int = 10
    max_retries: int = 2
    energy_budget: float = 1.0

    def exhausted(self, *, vlm_queries: int, search_cycles: int, retries: int) -> bool:
        return (
            vlm_queries >= self.max_vlm_queries
            or search_cycles >= self.max_camera_search_cycles
            or retries >= self.max_retries
        )


class InformationGainScorer:
    """Score a candidate perception action (doc 04 Step 7):

    ``expected_decision_improvement / (latency + energy + risk)``
    """

    def score(self, *, decision_improvement: float, latency_s: float, energy: float, risk: float) -> float:
        denominator = max(1e-6, latency_s + energy + risk)
        return decision_improvement / denominator


# ---------------------------------------------------------------------------
# Active search (doc 04 Step 6)
# ---------------------------------------------------------------------------


@dataclass
class SearchOutcome:
    query_id: str
    found: bool
    best: DetectionBox | None
    attempts: int
    reason: str = ""                    # found | no_match | budget_exhausted | model_unavailable
    uncertainty: float = 1.0            # 1.0 = nothing known; shrinks with attempts

    def snapshot(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id, "found": self.found,
            "best": self.best.snapshot() if self.best else None,
            "attempts": self.attempts, "reason": self.reason,
            "uncertainty": round(self.uncertainty, 4),
        }


class ActiveSearch:
    """Bounded active search: query → validate → retry/stop (doc 04 Step 6).

    Never hallucinates success: when the budget is exhausted, the outcome is
    ``found=False`` with ``reason="budget_exhausted"`` and a not-found
    uncertainty estimate — the planner sees missing information, not a lie.
    """

    def __init__(self, backend: LocateBackend, *, budget: PerceptionBudget | None = None,
                 parser: StrictBoxParser | None = None, model_version: str = "deterministic") -> None:
        self.backend = backend
        self.budget = budget or PerceptionBudget()
        self.parser = parser or StrictBoxParser()
        self.model_version = model_version

    def search(self, query: PerceptionQuery, *, image: Any, cycle: int = 0) -> SearchOutcome:
        vlm_queries = 0
        retries = 0
        attempts = 0
        best: DetectionBox | None = None

        while not self.budget.exhausted(vlm_queries=vlm_queries, search_cycles=attempts, retries=retries):
            attempts += 1
            result = self.backend.locate(image, query, cycle=cycle)
            vlm_queries += 1

            if result.failure_reason in ("model_unavailable", "timeout"):
                retries += 1
                continue

            boxes: list[DetectionBox] = []
            malformed = False
            for raw in result.boxes:
                # boxes may be DetectionBox instances (typed backend) or raw
                # model outputs (strict parsing path).
                if isinstance(raw, DetectionBox):
                    boxes.append(raw)
                    continue
                parsed, error = self.parser.parse(raw, source="locate_anything", model_version=result.model_version)
                if parsed is None:
                    malformed = True
                    continue
                boxes.append(parsed)
            if malformed:
                retries += 1
                continue

            if boxes:
                best = max(boxes, key=lambda b: b.confidence)
                if best.confidence >= query.confidence_threshold:
                    return SearchOutcome(query.query_id, True, best, attempts,
                                         reason="found", uncertainty=1.0 - best.confidence)
                # Below threshold: keep searching (ambiguous).
                continue

            # No match in this frame: the search belief widens.
            if result.not_found_reason == "no_match":
                continue

        # Budget exhausted or nothing found: report uncertainty, never success.
        uncertainty = max(0.0, 1.0 - attempts / max(1, self.budget.max_vlm_queries))
        reason = "budget_exhausted" if self.budget.exhausted(
            vlm_queries=vlm_queries, search_cycles=attempts, retries=retries) else "no_match"
        return SearchOutcome(query.query_id, False, best, attempts,
                             reason=reason, uncertainty=uncertainty)


# ---------------------------------------------------------------------------
# Escalation ladder (doc 04 Step 10)
# ---------------------------------------------------------------------------


@dataclass
class EscalationResult:
    step: str                # ssdlite | tracking | vlm | viewpoint | human
    satisfied: bool
    observation: DetectionBox | None = None

    def snapshot(self) -> dict[str, Any]:
        return {"step": self.step, "satisfied": self.satisfied,
                "observation": self.observation.snapshot() if self.observation else None}


class PerceptionEscalator:
    """Monotonic escalation: fast detector → tracking → VLM → viewpoint → human.

    Stops as soon as confidence is sufficient or the budget is exhausted.
    """

    LADDER: tuple[str, ...] = ("ssdlite", "tracking", "vlm", "viewpoint", "human")

    def __init__(self, *, confidence_threshold: float = 0.5) -> None:
        self.confidence_threshold = confidence_threshold

    def escalate(self, *, detector_confidence: float | None, tracked: bool, vlm_confidence: float | None,
                 budget_left: bool) -> EscalationResult:
        if detector_confidence is not None and detector_confidence >= self.confidence_threshold:
            return EscalationResult("ssdlite", True)
        if tracked:
            return EscalationResult("tracking", True)
        if vlm_confidence is not None and vlm_confidence >= self.confidence_threshold:
            return EscalationResult("vlm", True)
        if budget_left:
            return EscalationResult("viewpoint", False)
        return EscalationResult("human", False, None)
