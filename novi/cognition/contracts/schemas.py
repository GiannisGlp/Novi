"""JSON Schema generation for the typed cognition contracts (doc 26 §19, §22).

The typed implementation is the source of truth; JSON Schema is generated from
it for interoperability (never hand-maintained in a second incompatible
hierarchy). Schemas are generated deterministically from the Pydantic models.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from novi.cognition.contracts.attention import AttentionCandidate
from novi.cognition.contracts.decision import CognitiveDecisionRecord
from novi.cognition.contracts.entity import Entity, Relation
from novi.cognition.contracts.events import CognitiveEvent
from novi.cognition.contracts.evidence import Evidence
from novi.cognition.contracts.intent import IntentHypothesis
from novi.cognition.contracts.observation import Observation
from novi.cognition.contracts.prediction import Prediction
from novi.cognition.contracts.situation_state import PersonContext, SituationState
from novi.cognition.contracts.world_state import WorldState

# Canonical typed objects (doc 26 §6), keyed by contract_type for registry use.
CANONICAL_MODELS: dict[str, type[BaseModel]] = {
    "Observation": Observation,
    "Evidence": Evidence,
    "Entity": Entity,
    "Relation": Relation,
    "WorldState": WorldState,
    "SituationState": SituationState,
    "PersonContext": PersonContext,
    "AttentionCandidate": AttentionCandidate,
    "IntentHypothesis": IntentHypothesis,
    "Prediction": Prediction,
    "CognitiveDecisionRecord": CognitiveDecisionRecord,
    "CognitiveEvent": CognitiveEvent,
}

# contract_id → model, matching contracts/registry.json naming conventions.
CANONICAL_CONTRACT_IDS: dict[str, type[BaseModel]] = {
    "novi.observation": Observation,
    "novi.evidence": Evidence,
    "novi.entity": Entity,
    "novi.relationship": Relation,
    "novi.world-state": WorldState,
    "novi.situation-state": SituationState,
    "novi.person-context": PersonContext,
    "novi.attention-candidate": AttentionCandidate,
    "novi.intent-hypothesis": IntentHypothesis,
    "novi.prediction": Prediction,
    "novi.cognitive-decision-record": CognitiveDecisionRecord,
    "novi.cognitive-event": CognitiveEvent,
}


def generate_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Generate a JSON Schema (Draft 2020-12) for a canonical model."""
    schema = model.model_json_schema()
    schema.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
    schema["title"] = getattr(model, "CONTRACT_TYPE", model.__name__)
    return schema


def generate_all_schemas() -> dict[str, dict[str, Any]]:
    """Generate schemas for every canonical cognitive object."""
    return {name: generate_schema(model) for name, model in CANONICAL_MODELS.items()}


def schema_json(model: type[BaseModel], *, indent: int = 2) -> str:
    return json.dumps(generate_schema(model), indent=indent)


def all_schemas_json(*, indent: int = 2) -> str:
    return json.dumps(generate_all_schemas(), indent=indent)
