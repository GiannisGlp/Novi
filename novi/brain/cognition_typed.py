"""Typed cognitive emission for the Mac Brain (roadmap item 12).

Converts the legacy in-memory cognition output (Situation + ReasoningResult)
into the canonical typed cognition contracts (doc 26):

  - SituationState (`situation_state.py`)
  - PersonContext per participant (`situation_state.py`)
  - IntentHypothesis from hypotheses/relations
  - Prediction from causal/temporal inferences (predicted never observed)
  - CognitiveDecisionRecord from the refined interpretation
  - CognitiveEvent wrapping the created objects (replay/observability)

Cognition remains an interpretation layer: nothing produced here is an
authorization grant, an action proposal, or a physical command.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from novi.cognition.contracts.common import Provenance, Uncertainty
from novi.cognition.contracts.decision import CognitiveDecisionRecord
from novi.cognition.contracts.events import CognitiveEvent
from novi.cognition.contracts.intent import IntentHypothesis
from novi.cognition.contracts.prediction import Prediction
from novi.cognition.contracts.situation_state import PersonContext, SituationState


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _provenance(source: str = "cognition") -> Provenance:
    return Provenance(source=source)


def _uncertainty(confidence: float) -> Uncertainty:
    return Uncertainty(confidence=confidence)


def _competing_alternatives(idx: int, hypotheses: Any, inferences: Any = ()) -> list[str]:
    """Real competing hypotheses for hypothesis ``idx`` (never hard-coded empty).

    Each IntentHypothesis carries the other candidate explanations as its
    alternatives so downstream consumers can weigh rivals; confidence and
    provenance ride on the hypothesis itself (confidence/uncertainty/provenance
    plus supporting_evidence_ids). Bounded to 3 rivals, topped up from causal
    inferences when fewer rivals exist, with a deterministic honest fallback
    when the cycle produced a single hypothesis.
    """
    texts = [str(h.get("hypothesis", "")) for h in (hypotheses or [])]
    alts = [t[:80] for j, t in enumerate(texts) if j != idx and t][:3]
    for inf in inferences or ():
        if len(alts) >= 3:
            break
        s = str(inf)[:80]
        if s and s not in alts:
            alts.append(s)
    if not alts:
        alts = ["no_competing_hypothesis_observed"]
    return alts


class TypedCognitionOutput:
    """Container for one cycle's typed cognitive contracts."""

    __slots__ = ("situation", "person_contexts", "predictions",
                 "intent_hypotheses", "decision", "events", "correlation_id")

    def __init__(self, *, correlation_id: str) -> None:
        self.correlation_id = correlation_id
        self.situation: SituationState | None = None
        self.person_contexts: list[PersonContext] = []
        self.predictions: list[Prediction] = []
        self.intent_hypotheses: list[IntentHypothesis] = []
        self.decision: CognitiveDecisionRecord | None = None
        self.events: list[CognitiveEvent] = []

    def snapshot(self, *, include_events: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "correlation_id": self.correlation_id,
            "situation": self.situation.model_dump(mode="json") if self.situation else None,
            "person_contexts": [p.model_dump(mode="json") for p in self.person_contexts],
            "predictions": [p.model_dump(mode="json") for p in self.predictions],
            "intent_hypotheses": [h.model_dump(mode="json") for h in self.intent_hypotheses],
            "decision": self.decision.model_dump(mode="json") if self.decision else None,
        }
        if include_events:
            out["events"] = [e.model_dump(mode="json") for e in self.events]
        return out

    def all_objects(self) -> list[Any]:
        objs: list[Any] = []
        if self.situation:
            objs.append(self.situation)
        objs.extend(self.person_contexts)
        objs.extend(self.predictions)
        objs.extend(self.intent_hypotheses)
        if self.decision:
            objs.append(self.decision)
        return objs


def emit_cognitive_typed(
    situation: Any,
    reasoning: Any,
    *,
    cycle: int,
    world_revision: int = 0,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> TypedCognitionOutput:
    """Build the typed contracts for one cognition cycle.

    `situation`/`reasoning` are the legacy `Situation`/`ReasoningResult`
    dataclasses from `brain.b1_cognition` (or compatible structs).
    """
    rid = correlation_id or uuid4().hex
    now = _now()
    out = TypedCognitionOutput(correlation_id=rid)

    participants = sorted(set(situation.salient_entities))
    out.situation = SituationState(
        id=f"sit-{cycle}-{rid[:8]}",
        world_revision=world_revision,
        created_at=now,
        participants=participants,
        likely_addressees=[p for p in participants if p in situation.salient_entities][:3],
        current_activity=reasoning.conclusion,
        salient_events=list(situation.recent_events),
        social_context={"relations": len(situation.relations), "recalled": len(situation.recalled)},
        goal_hypotheses=[h.get("hypothesis", "") for h in reasoning.hypotheses][:5],
        risks=list(situation.uncertainty),
        uncertainty={"low_confidence": len(situation.uncertainty) > 0},
        source="cognition",
        provenance=_provenance(),
        correlation_id=rid,
        causation_id=causation_id,
    )

    # PersonContext per salient person-like participant.
    person_tags = {e for e in participants if e != "speech"}
    speech_observed = "speech" in situation.salient_entities
    for idx, person in enumerate(sorted(person_tags)):
        confidence = next(
            (max(0.05, getattr(e, "confidence", 0.5)) for e in situation.entities if getattr(e, "entity", "") == person),
            0.5,
        )
        out.person_contexts.append(PersonContext(
            id=f"pc-{cycle}-{rid[:8]}-{idx}",
            person_ref=person,
            created_at=now,
            presence_confidence=round(confidence, 3),
            identity_confidence=round(confidence, 3),
            attention_cues=situation.recent_events[:2],
            speech_cues=["speech_observed"] if speech_observed else [],
            addressee_cues=[],  # addressee discrimination happens in autonomy/chat
            relationship_category=None,
            authorized_interaction=False,  # governance decides
            source_evidence_ids=[e.source for e in situation.evidence][:4],
            source="cognition",
            provenance=_provenance(),
            correlation_id=rid,
            causation_id=causation_id,
        ))

    # Intent hypotheses from knowledge relations / goal context.
    for idx, hyp in enumerate(reasoning.hypotheses):
        out.intent_hypotheses.append(IntentHypothesis(
            id=f"i-{cycle}-{rid[:8]}-{idx}",
            created_at=now,
            actor_ref=participants[0] if participants else "unknown",
            intent=hyp.get("hypothesis", "unknown")[:80],
            confidence=round(min(1.0, max(0.0, float(hyp.get("confidence", 0.5)))), 3),
            uncertainty=_uncertainty(float(hyp.get("confidence", 0.5))),
            alternatives=_competing_alternatives(idx, reasoning.hypotheses, reasoning.inferences),
            supporting_evidence_ids=[e.source for e in situation.evidence][:3],
            source="cognition",
            provenance=_provenance(),
            correlation_id=rid,
            causation_id=causation_id,
        ))

    # Predictions from temporal/causal inferences — always PREDICTED.
    for idx, inf in enumerate(reasoning.inferences):
        out.predictions.append(Prediction(
            id=f"pred-{rid[:8]}-{idx}",
            created_at=now,
            predicts_at=_now(),
            subject_ref=participants[0] if participants else "world",
            predicted_attribute="activity",
            predicted_value=inf,
            confidence=0.6,
            uncertainty=_uncertainty(0.6),
            basis="observed_pattern",
            supporting_evidence_ids=[e.source for e in situation.evidence][:3],
            source="cognition",
            provenance=_provenance(),
            correlation_id=rid,
            causation_id=causation_id,
        ))

    # Decision record: interpretation only (never authorization).
    out.decision = CognitiveDecisionRecord(
        id=f"dec-{cycle}-{rid[:8]}",
        created_at=now,
        situation_ref=out.situation.id,
        interpretation=reasoning.conclusion,
        alternatives=[h.get("hypothesis", "") for h in reasoning.hypotheses][:3],
        uncertainty={"confidence": round(reasoning.confidence, 3)},
        rationale_refs=[e.source for e in situation.evidence][:4],
        recommended_next_states=list(reasoning.inferences)[:3],
        model_refs=["deterministic-cognition"],
        policy_constraints_observed=["no_escalation", "interpretation_only"],
        source="cognition",
        provenance=_provenance(),
        correlation_id=rid,
        causation_id=causation_id,
    )
    # The record MUST be an interpretation only (ownership invariant).
    assert out.decision.is_interpretation_only

    # Cognitive events (observable transitions for replay).
    out.events.append(CognitiveEvent(
        id=f"evt-{cycle}-{rid[:8]}",
        event_type="situation_updated",
        occurred_at=now,
        object_refs=[out.situation.id],
        detail={"cycle": cycle, "conclusion": reasoning.conclusion},
        correlation_id=rid,
        causation_id=causation_id,
        provenance=_provenance(),
    ))
    if out.decision is not None:
        out.events.append(CognitiveEvent(
            id=f"evt-dec-{cycle}-{rid[:8]}",
            event_type="decision_recorded",
            occurred_at=now,
            object_refs=[out.decision.id],
            detail={"cycle": cycle},
            correlation_id=rid,
            causation_id=causation_id,
            provenance=_provenance(),
        ))
    return out
