"""Replay fixtures for the typed cognition contracts (doc 26 §20).

Deterministic fixtures for the 12 canonical scenarios. Fixtures use structured
observations/evidence rather than private raw media. Each fixture is a JSON
payload the loader/runner can replay through the validation pipeline.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)


def _ts(offset_minutes: int) -> str:
    return (NOW + timedelta(minutes=offset_minutes)).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Scenario catalog (doc 26 §20, 12 scenarios)
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict[str, Any]] = {}


def _scenario(scenario_id: str, description: str, events: list[dict[str, Any]], *, expect_valid: bool = True) -> None:
    SCENARIOS[scenario_id] = {
        "scenario_id": scenario_id,
        "description": description,
        "events": events,
        "expect_valid": expect_valid,
    }


# 1. unknown person enters room
_scenario(
    "s01-unknown-person-enters-room",
    "An unknown person enters the room; camera reports a person-shaped detection with low identity confidence.",
    [
        {
            "contract_type": "Observation",
            "id": "obs-001",
            "modality": "camera",
            "sensor_id": "cam_front",
            "sensor_time": _ts(-2),
            "receive_time": _ts(-1),
            "clock_domain": "sensor",
            "frame_id": "cam_front",
            "payload_ref": "det:person-shape-001",
            "quality": {"iou": 0.82},
            "source": "perception",
            "provenance": {"source": "perception", "source_observation_ids": []},
        },
        {
            "contract_type": "Evidence",
            "id": "ev-001",
            "type": "presence",
            "subject_ref": "entity-person-unknown-001",
            "attributes": {"appearance": "person-shaped"},
            "confidence": 0.8,
            "uncertainty": {"confidence": 0.8, "calibrated": False},
            "source_observation_ids": ["obs-001"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-001"]},
            "privacy": {"classification": "required"},
        },
        {
            "contract_type": "PersonContext",
            "id": "pc-001",
            "person_ref": "entity-person-unknown-001",
            "created_at": _ts(-1),
            "presence_confidence": 0.8,
            "identity_confidence": 0.1,
            "source_evidence_ids": ["ev-001"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_evidence_ids": ["ev-001"]},
            "privacy": {"classification": "required"},
        },
    ],
)

# 2. known person identified with multimodal evidence
_scenario(
    "s02-known-person-multimodal",
    "A known person is identified from camera + audio evidence.",
    [
        {
            "contract_type": "Observation",
            "id": "obs-002a",
            "modality": "camera",
            "sensor_id": "cam_front",
            "sensor_time": _ts(-4),
            "receive_time": _ts(-3),
            "clock_domain": "sensor",
            "payload_ref": "det:face-002",
            "quality": {"face_confidence": 0.9},
            "source": "perception",
            "provenance": {"source": "perception"},
        },
        {
            "contract_type": "Observation",
            "id": "obs-002b",
            "modality": "audio",
            "sensor_id": "mic_main",
            "sensor_time": _ts(-3),
            "receive_time": _ts(-2),
            "clock_domain": "sensor",
            "payload_ref": "stt:utterance-002",
            "quality": {"confidence": 0.95},
            "source": "perception",
            "provenance": {"source": "perception"},
        },
        {
            "contract_type": "Evidence",
            "id": "ev-002",
            "type": "identity_hypothesis",
            "subject_ref": "entity-person-alice",
            "attributes": {"name_hypothesis": "alice", "face_score": 0.9, "voice_score": 0.95},
            "confidence": 0.93,
            "uncertainty": {"confidence": 0.93, "calibrated": True},
            "source_observation_ids": ["obs-002a", "obs-002b"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-002a", "obs-002b"]},
            "privacy": {"classification": "required"},
        },
    ],
)

# 3. five-person conversation where Novi is not addressed
_scenario(
    "s03-five-person-not-addressed",
    "Five people talk; addressee cues indicate Novi is not addressed.",
    [
        {
            "contract_type": "SituationState",
            "id": "sit-003",
            "world_revision": 7,
            "created_at": _ts(-1),
            "participants": ["p1", "p2", "p3", "p4", "p5"],
            "likely_addressees": [],
            "current_activity": "group_conversation",
            "social_context": {"novi_addressed": False},
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-003"]},
        }
    ],
)

# 4. person directly addresses Novi
_scenario(
    "s04-person-addresses-novi",
    "A person directly addresses Novi.",
    [
        {
            "contract_type": "SituationState",
            "id": "sit-004",
            "world_revision": 8,
            "created_at": _ts(-1),
            "participants": ["p1"],
            "likely_addressees": ["novi"],
            "current_activity": "direct_address",
            "social_context": {"novi_addressed": True},
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-004"]},
        },
        {
            "contract_type": "IntentHypothesis",
            "id": "int-004",
            "created_at": _ts(-1),
            "actor_ref": "p1",
            "intent": "requesting_attention",
            "confidence": 0.85,
            "uncertainty": {"confidence": 0.85, "calibrated": False},
            "supporting_evidence_ids": ["ev-004"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_evidence_ids": ["ev-004"]},
        },
    ],
)

# 5. ambiguous addressee
_scenario(
    "s05-ambiguous-addressee",
    "Addressee is ambiguous between Novi and another person.",
    [
        {
            "contract_type": "SituationState",
            "id": "sit-005",
            "world_revision": 9,
            "created_at": _ts(-1),
            "participants": ["p1", "p2"],
            "likely_addressees": ["novi", "p2"],
            "current_activity": "ambiguous_address",
            "social_context": {"novi_addressed": None},
            "uncertainty": {"addressee": 0.5},
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-005"]},
        }
    ],
)

# 6. contradictory camera/audio evidence
_scenario(
    "s06-contradictory-evidence",
    "Camera suggests person A, audio suggests person B for the same event.",
    [
        {
            "contract_type": "Evidence",
            "id": "ev-006a",
            "type": "identity_hypothesis",
            "subject_ref": "person-a",
            "attributes": {"face_score": 0.7},
            "confidence": 0.7,
            "uncertainty": {"confidence": 0.7, "calibrated": False},
            "source_observation_ids": ["obs-006a"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-006a"]},
        },
        {
            "contract_type": "Evidence",
            "id": "ev-006b",
            "type": "identity_hypothesis",
            "subject_ref": "person-b",
            "attributes": {"voice_score": 0.75},
            "confidence": 0.75,
            "uncertainty": {"confidence": 0.75, "calibrated": False},
            "source_observation_ids": ["obs-006b"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-006b"]},
        },
    ],
    expect_valid=True,  # contradictions are preserved, not rejected
)

# 7. stale world-state evidence
_scenario(
    "s07-stale-world-state",
    "Evidence refers to a world revision that no longer exists.",
    [
        {
            "contract_type": "SituationState",
            "id": "sit-007",
            "world_revision": 99,  # stale/unknown revision
            "created_at": _ts(-30),
            "participants": [],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_observation_ids": ["obs-007"]},
        }
    ],
    expect_valid=True,  # structurally valid; staleness is a semantic flag
)

# 8. reasoning model returns malformed JSON
_scenario(
    "s08-malformed-model-output",
    "Reasoning model returns malformed JSON; the structured-output validator must reject it.",
    [
        {
            "contract_type": "CognitiveEvent",
            "id": "evt-008",
            "event_type": "cognitive_error",
            "occurred_at": _ts(-1),
            "detail": {"error": "model_output_not_valid_json"},
            "source": "cognition",
            "provenance": {"source": "cognition", "model_ref": "ollama:qwen3.8", "model_version": "3.8", "transformation": "structured-output"},
        }
    ],
)

# 9. reasoning model unavailable
_scenario(
    "s09-model-unavailable",
    "The reasoning model is unavailable; the runtime degrades gracefully.",
    [
        {
            "contract_type": "CognitiveEvent",
            "id": "evt-009",
            "event_type": "cognitive_error",
            "occurred_at": _ts(-1),
            "detail": {"error": "model_unavailable", "fallback": "deterministic"},
            "source": "cognition",
            "provenance": {"source": "cognition", "model_ref": "ollama:qwen3.8", "model_version": "3.8", "transformation": "fallback"},
        }
    ],
)

# 10. memory unavailable
_scenario(
    "s10-memory-unavailable",
    "Memory subsystem unavailable; cognition continues without recall.",
    [
        {
            "contract_type": "CognitiveEvent",
            "id": "evt-010",
            "event_type": "cognitive_error",
            "occurred_at": _ts(-1),
            "detail": {"error": "memory_unavailable", "degraded": True},
            "source": "cognition",
            "provenance": {"source": "cognition"},
        }
    ],
)

# 11. privacy-filtered context
_scenario(
    "s11-privacy-filtered-context",
    "Context is privacy-filtered; sensitive fields must stay classified.",
    [
        {
            "contract_type": "PersonContext",
            "id": "pc-011",
            "person_ref": "entity-person-alice",
            "created_at": _ts(-1),
            "presence_confidence": 0.9,
            "identity_confidence": 0.88,
            "relationship_category": "friend",
            "source": "cognition",
            "provenance": {"source": "cognition", "source_evidence_ids": ["ev-011"]},
            "privacy": {"classification": "required", "sensitive_fields": ["person_ref", "identity_confidence"]},
        }
    ],
)

# 12. action proposal returned to Autonomy without Cognition bypassing policy
_scenario(
    "s12-action-proposal-no-bypass",
    "Cognition produces a CognitiveDecisionRecord; the action proposal belongs to Autonomy.",
    [
        {
            "contract_type": "CognitiveDecisionRecord",
            "id": "cdr-012",
            "created_at": _ts(-1),
            "situation_ref": "sit-012",
            "interpretation": "user appears to be requesting the cup",
            "alternatives": ["user is pointing", "user is leaving"],
            "rationale_refs": ["ev-012"],
            "recommended_next_states": ["offer_cup"],
            "source": "cognition",
            "provenance": {"source": "cognition", "source_evidence_ids": ["ev-012"]},
        }
    ],
)


def all_scenarios() -> list[dict[str, Any]]:
    """Return all 12 scenario fixtures in canonical order."""
    ordered = [f"s{i:02d}" for i in range(1, 13)]

    def order_key(key: str) -> int:
        for i, prefix in enumerate(ordered):
            if key.startswith(prefix):
                return i
        return 99

    return [SCENARIOS[key] for key in sorted(SCENARIOS, key=order_key)]


if __name__ == "__main__":
    import json

    print(json.dumps(all_scenarios(), indent=2, default=str))
