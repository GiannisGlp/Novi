"""Contract tests for the typed cognition layer (doc 26 §21 invariants).

Covers construction, serialization round-trip, JSON Schema generation, and the
full validation pipeline (structural / semantic / provenance / cross-contract),
plus replay of all 12 canonical scenarios.
"""

from __future__ import annotations

import json
import unittest

from cognition.contracts import (
    CognitiveDecisionRecord,
    Entity,
    Evidence,
    Observation,
    Relation,
    SchemaVersion,
    WorldState,
)
from cognition.contracts.schemas import CANONICAL_MODELS, generate_all_schemas, generate_schema
from cognition.replay.runner import replay_all, summarize
from cognition.validation import (
    SemanticContext,
    validate_cross_contract,
    validate_full,
    validate_provenance,
    validate_semantic,
    validate_structurally,
)


def _obs(obs_id: str = "obs-001", **kw) -> dict:
    base = {
        "id": obs_id,
        "modality": "camera",
        "sensor_id": "cam_front",
        "sensor_time": "2026-08-22T11:58:00+00:00",
        "receive_time": "2026-08-22T11:59:00+00:00",
        "clock_domain": "sensor",
        "frame_id": "cam_front",
        "payload_ref": "det:001",
        "source": "perception",
    }
    base.update(kw)
    return base


class CanonicalObjectTests(unittest.TestCase):
    def test_all_twelve_models_registered(self):
        self.assertEqual(
            set(CANONICAL_MODELS),
            {
                "Observation", "Evidence", "Entity", "Relation", "WorldState",
                "SituationState", "PersonContext", "AttentionCandidate",
                "IntentHypothesis", "Prediction", "CognitiveDecisionRecord",
                "CognitiveEvent",
            },
        )

    def test_observation_construction(self):
        obs = Observation(**_obs())
        self.assertEqual(obs.modality, "camera")
        self.assertEqual(obs.contract_type, "Observation")
        self.assertEqual(str(obs.schema_version), "1.0.0")

    def test_observation_rejects_semantic_overclaiming_field(self):
        # "Vano is present" is not an Observation field; extra fields are forbidden.
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            Observation(**_obs(**{"person_present": "Vano"}))

    def test_entity_stable_id_independent_of_name(self):
        entity = Entity(id="person_123", kind="person", name="alice")
        self.assertEqual(entity.id, "person_123")
        self.assertEqual(entity.name, "alice")
        # Changing the label must not change identity.
        entity2 = Entity(id="person_123", kind="person", name="Alice")
        self.assertEqual(entity.id, entity2.id)

    def test_relation_references_entity_ids(self):
        rel = Relation(id="rel-1", subject_ref="person_123", predicate="looking_at", object_ref="robot_001")
        self.assertEqual(rel.subject_ref, "person_123")
        self.assertEqual(rel.object_ref, "robot_001")

    def test_world_state_revisioned(self):
        ws = WorldState(id="ws-1", revision=3, created_at="2026-08-22T12:00:00+00:00")
        self.assertEqual(ws.revision, 3)

    def test_schema_version_parse_and_validation(self):
        v = SchemaVersion.parse("2.1.0")
        self.assertEqual((v.major, v.minor, v.patch), (2, 1, 0))
        with self.assertRaises(ValueError):
            SchemaVersion.parse("not-a-version")

    def test_serialization_round_trip(self):
        obs = Observation(**_obs())
        dumped = obs.model_dump(mode="json")
        restored = Observation.model_validate(dumped)
        self.assertEqual(restored.id, obs.id)
        self.assertEqual(restored.sensor_time, obs.sensor_time)


class SchemaGenerationTests(unittest.TestCase):
    def test_all_schemas_generate(self):
        schemas = generate_all_schemas()
        self.assertEqual(len(schemas), 12)

    def test_schema_has_contract_fields(self):
        schema = generate_schema(Observation)
        props = schema["properties"]
        self.assertIn("modality", props)
        self.assertIn("sensor_id", props)
        self.assertIn("payload_ref", props)

    def test_schema_is_draft_2020_12(self):
        schema = generate_schema(Evidence)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_schemas_json_serializable(self):
        json.dumps(generate_all_schemas())


class StructuralValidationTests(unittest.TestCase):
    def test_valid_payload_passes(self):
        result = validate_structurally("Observation", _obs())
        self.assertTrue(result.valid)
        self.assertEqual(result.value["id"], "obs-001")

    def test_missing_required_field_fails(self):
        raw = _obs()
        del raw["payload_ref"]
        result = validate_structurally("Observation", raw)
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "field_invalid" for i in result.issues))

    def test_unknown_contract_type_fails(self):
        result = validate_structurally("NotAContract", {})
        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].category, "schema_invalid")

    def test_wrong_type_fails(self):
        raw = _obs()
        raw["modality"] = 42
        result = validate_structurally("Observation", raw)
        self.assertFalse(result.valid)

    def test_typed_instance_accepted(self):
        obs = Observation(**_obs())
        result = validate_structurally("Observation", obs)
        self.assertTrue(result.valid)


class SemanticValidationTests(unittest.TestCase):
    def test_unknown_entity_ref_fails_when_resolution_required(self):
        ctx = SemanticContext(entity_ids={"known"}, allow_unresolved=False)
        result = validate_semantic(
            {"contract_type": "Relation", "subject_ref": "ghost", "predicate": "near", "object_ref": "known"},
            ctx,
        )
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "reference_invalid" for i in result.issues))

    def test_unresolved_refs_allowed_by_default(self):
        result = validate_semantic(
            {"contract_type": "Relation", "subject_ref": "ghost", "predicate": "near", "object_ref": "other"},
        )
        self.assertTrue(result.valid)

    def test_invalid_validity_interval(self):
        result = validate_semantic(
            {
                "contract_type": "Evidence",
                "valid_from": "2026-08-22T12:00:00+00:00",
                "valid_until": "2026-08-22T11:00:00+00:00",
            }
        )
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "time_invalid" for i in result.issues))

    def test_receive_before_sensor_rejected(self):
        result = validate_semantic(
            {
                "contract_type": "Observation",
                "sensor_time": "2026-08-22T12:00:00+00:00",
                "receive_time": "2026-08-22T11:00:00+00:00",
            }
        )
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "time_invalid" for i in result.issues))

    def test_confidence_out_of_range(self):
        result = validate_semantic({"contract_type": "Evidence", "confidence": 1.5})
        self.assertFalse(result.valid)

    def test_prediction_before_creation_rejected(self):
        result = validate_semantic(
            {
                "contract_type": "Prediction",
                "created_at": "2026-08-22T12:00:00+00:00",
                "predicts_at": "2026-08-22T11:00:00+00:00",
            }
        )
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "time_invalid" for i in result.issues))


class ProvenanceValidationTests(unittest.TestCase):
    def test_decision_relevant_without_provenance_rejected(self):
        result = validate_provenance({"contract_type": "Evidence", "source": "system"})
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "provenance_missing" for i in result.issues))

    def test_evidence_with_observation_chain_passes(self):
        result = validate_provenance(
            {
                "contract_type": "Evidence",
                "source": "cognition",
                "provenance": {"source": "cognition", "source_observation_ids": ["obs-001"]},
            }
        )
        self.assertTrue(result.valid)

    def test_model_derived_requires_version_and_transformation(self):
        result = validate_provenance(
            {
                "contract_type": "Evidence",
                "source": "cognition",
                "provenance": {
                    "source": "cognition",
                    "model_ref": "ollama:qwen3.8",
                    "model_version": None,
                    "transformation": None,
                },
            }
        )
        self.assertFalse(result.valid)
        self.assertTrue(any("model_version" in i.message for i in result.issues))

    def test_transient_observation_tolerates_thin_provenance(self):
        result = validate_provenance({"contract_type": "Observation", "source": "perception"})
        self.assertTrue(result.valid)


class CrossContractValidationTests(unittest.TestCase):
    def test_cognition_cannot_author_authorization(self):
        result = validate_cross_contract({"contract_type": "AuthorizationDecision", "decision": "ALLOW"})
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "ownership_violation" for i in result.issues))

    def test_cognition_cannot_author_action_execution(self):
        result = validate_cross_contract({"contract_type": "ActionExecution", "action": "move"})
        self.assertFalse(result.valid)

    def test_decision_record_passes(self):
        record = CognitiveDecisionRecord(
            id="cdr-1",
            created_at="2026-08-22T12:00:00+00:00",
            situation_ref="sit-1",
            interpretation="user requests the cup",
        )
        result = validate_cross_contract(record)
        self.assertTrue(result.valid)

    def test_person_context_requires_privacy_classification(self):
        result = validate_cross_contract(
            {
                "contract_type": "PersonContext",
                "person_ref": "p1",
                "identity_confidence": 0.9,
                "privacy": {"classification": "inherited"},
            }
        )
        self.assertFalse(result.valid)
        self.assertTrue(any(i.category == "privacy_invalid" for i in result.issues))


class FullPipelineTests(unittest.TestCase):
    def test_evidence_full_pipeline_passes(self):
        raw = {
            "contract_type": "Evidence",
            "id": "ev-1",
            "type": "presence",
            "subject_ref": "person_123",
            "attributes": {"appearance": "person-shaped"},
            "confidence": 0.8,
            "uncertainty": {"confidence": 0.8, "calibrated": False},
            "source_observation_ids": ["obs-001"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-001"]},
        }
        structural, semantic, provenance, cross = validate_full(raw)
        self.assertTrue(structural.valid)
        self.assertTrue(semantic.valid)
        self.assertTrue(provenance.valid)
        self.assertTrue(cross.valid)

    def test_bad_payload_short_circuits(self):
        structural, semantic, provenance, cross = validate_full({"contract_type": "Observation", "id": 42})
        self.assertFalse(structural.valid)


class ReplayTests(unittest.TestCase):
    def test_all_twelve_scenarios_replay(self):
        summary = summarize(replay_all())
        self.assertEqual(summary["scenarios"], 12)
        self.assertEqual(summary["passed"], 12)
        self.assertEqual(summary["failed"], 0)


if __name__ == "__main__":
    unittest.main()
