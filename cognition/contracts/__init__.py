"""Typed cognition contract layer (docs/03-cognition/22, 25, 26; gap-analysis Step 1).

The typed boundary for canonical cognitive objects. Pydantic v2 models with
generated JSON Schema for interoperability.

Ownership invariants (doc 26 §17, §21):
- Cognition cannot create an authorization grant.
- Cognition cannot create a physical action command.
- No observation becomes a verified fact without an explicit promotion path.
"""

from __future__ import annotations

from cognition.contracts.attention import AttentionCandidate
from cognition.contracts.common import (
    CausationId,
    ClockDomain,
    ContractEnvelope,
    CorrelationId,
    Identifier,
    LifecycleState,
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
    SpatialReference,
    Timestamp,
    Uncertainty,
    ValidationErrorCategory,
    ValidationIssue,
    utc_now,
)
from cognition.contracts.common import (
    PrivacyClassification as PrivacyClassificationLiteral,
)
from cognition.contracts.decision import CognitiveDecisionRecord
from cognition.contracts.entity import Entity, Relation
from cognition.contracts.events import CognitiveEvent
from cognition.contracts.evidence import Evidence, EvidenceEnvelope
from cognition.contracts.intent import IntentHypothesis
from cognition.contracts.observation import Observation, ObservationEnvelope
from cognition.contracts.prediction import Prediction
from cognition.contracts.schemas import (
    CANONICAL_CONTRACT_IDS,
    CANONICAL_MODELS,
    generate_all_schemas,
    generate_schema,
)
from cognition.contracts.situation_state import PersonContext, SituationState
from cognition.contracts.world_state import WorldState

__all__ = [
    "ClockDomain",
    "ContractEnvelope",
    "CorrelationId",
    "CausationId",
    "Identifier",
    "LifecycleState",
    "PrivacyClassificationLiteral",
    "PrivacyClassificationModel",
    "Provenance",
    "SchemaVersion",
    "SpatialReference",
    "Timestamp",
    "Uncertainty",
    "ValidationErrorCategory",
    "ValidationIssue",
    "utc_now",
    "Observation",
    "ObservationEnvelope",
    "Evidence",
    "EvidenceEnvelope",
    "Entity",
    "Relation",
    "WorldState",
    "SituationState",
    "PersonContext",
    "AttentionCandidate",
    "IntentHypothesis",
    "Prediction",
    "CognitiveDecisionRecord",
    "CognitiveEvent",
    "CANONICAL_CONTRACT_IDS",
    "CANONICAL_MODELS",
    "generate_all_schemas",
    "generate_schema",
]
