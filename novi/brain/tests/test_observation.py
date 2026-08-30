"""Tests for novi/brain/observation.py — canonical observation contract.

Plan 22 Phase 1 Task 1.1: every perception result normalizes into an
Observation carrying observation_id, timestamp, source, modality, entity
candidate, attributes, location, confidence, uncertainty, provenance and
epistemic status. Task 1.3: fusion may increase confidence / reduce
uncertainty but must never manufacture certainty.

Deterministic, hardware-free. Pure unit tests.
"""

from __future__ import annotations

import unittest

from novi.brain.observation import (
    EPISTEMIC_HYPOTHETICAL,
    EPISTEMIC_OBSERVED,
    EPISTEMIC_UNKNOWN,
    Observation,
    fuse_observations,
    make_observation,
    observation_from_grounding,
    observation_from_world_observation,
)


class _Track:
    def __init__(self, track_id, label, confidence, bbox=(0, 0, 10, 10)):
        self.track_id = track_id
        self.label = label
        self.last_confidence = confidence
        self.bbox = bbox


class _WorldObservation:
    def __init__(self, tracks, frame_id="frame-1", captured_at="2026-08-30T10:00:00Z"):
        self.tracks = tracks
        self.frame_id = frame_id
        self.captured_at = captured_at


class _GroundingObs:
    def __init__(self, label="mug", confidence=0.9, location=None, provenance="locate_anything"):
        self.label = label
        self.confidence = confidence
        self.location = location or {"frame": "camera", "x": 1.2, "y": 0.4}
        self.provenance = provenance
        self.timestamp = "2026-08-30T10:01:00Z"
        self.query = "the mug"


class ObservationContractTest(unittest.TestCase):
    def test_factory_fills_all_required_fields(self) -> None:
        obs = make_observation(
            source="front_camera",
            modality="vision",
            entity_candidate="person",
            confidence=0.97,
            provenance="front_camera:frame:18322",
        )
        self.assertTrue(obs.observation_id)
        self.assertEqual(obs.source, "front_camera")
        self.assertEqual(obs.modality, "vision")
        self.assertEqual(obs.entity_candidate, "person")
        self.assertEqual(obs.confidence, 0.97)
        self.assertEqual(obs.epistemic_status, EPISTEMIC_OBSERVED)
        # uncertainty defaults to 1 - confidence (matches WorldEntity sigma).
        self.assertAlmostEqual(obs.uncertainty, 0.03)
        self.assertEqual(obs.location, {})
        self.assertEqual(obs.attributes, {})

    def test_confidence_clamped_to_unit_interval(self) -> None:
        obs = make_observation(
            source="s", modality="vision", entity_candidate="x",
            confidence=1.7, provenance="p",
        )
        self.assertEqual(obs.confidence, 1.0)
        obs2 = make_observation(
            source="s", modality="vision", entity_candidate="x",
            confidence=-0.2, provenance="p",
        )
        self.assertEqual(obs2.confidence, 0.0)

    def test_timestamp_defaults_to_now_iso(self) -> None:
        obs = make_observation(
            source="s", modality="vision", entity_candidate="x",
            confidence=0.5, provenance="p",
        )
        self.assertIn("T", obs.timestamp)

    def test_epistemic_status_validated(self) -> None:
        with self.assertRaises(ValueError):
            make_observation(
                source="s", modality="vision", entity_candidate="x",
                confidence=0.5, provenance="p", epistemic_status="MAYBE",
            )

    def test_to_dict_round_trip(self) -> None:
        obs = make_observation(
            source="s", modality="vision", entity_candidate="mug",
            confidence=0.8, provenance="p", location={"frame": "map", "x": 1.0},
            identity_candidate="vano",
        )
        data = obs.to_dict()
        self.assertEqual(data["entity_candidate"], "mug")
        self.assertEqual(data["identity_candidate"], "vano")
        self.assertEqual(data["location"], {"frame": "map", "x": 1.0})
        self.assertAlmostEqual(data["uncertainty"], 0.2)
        # to_dict is the serialization boundary: a restored observation must
        # serialize identically (float rounding included).
        self.assertEqual(Observation(**data).to_dict(), data)


class WorldObservationNormalizationTest(unittest.TestCase):
    def test_tracks_become_observations_with_stable_entity_ids(self) -> None:
        wo = _WorldObservation(
            [_Track(3, "person", 0.96), _Track(4, "mug", 0.72)]
        )
        obs = observation_from_world_observation(wo)
        self.assertEqual(len(obs), 2)
        by_id = {o.entity_id: o for o in obs}
        self.assertEqual(by_id["track-3"].entity_candidate, "person")
        self.assertEqual(by_id["track-3"].confidence, 0.96)
        self.assertEqual(by_id["track-3"].modality, "vision")
        self.assertEqual(by_id["track-3"].source, wo.frame_id)
        self.assertEqual(by_id["track-3"].provenance, f"frame:{wo.frame_id}")
        self.assertEqual(by_id["track-3"].epistemic_status, EPISTEMIC_OBSERVED)
        self.assertEqual(by_id["track-4"].entity_candidate, "mug")

    def test_low_confidence_track_is_unknown_not_observed(self) -> None:
        wo = _WorldObservation([_Track(1, "person", 0.3)])
        obs = observation_from_world_observation(wo)[0]
        self.assertEqual(obs.epistemic_status, EPISTEMIC_UNKNOWN)

    def test_empty_tracks_produce_empty_list(self) -> None:
        self.assertEqual(observation_from_world_observation(_WorldObservation([])), [])


class GroundingNormalizationTest(unittest.TestCase):
    def test_grounding_observation_normalizes_as_hypothetical(self) -> None:
        g = _GroundingObs()
        obs = observation_from_grounding(g)
        self.assertEqual(obs.entity_candidate, "mug")
        self.assertEqual(obs.confidence, 0.9)
        self.assertEqual(obs.epistemic_status, EPISTEMIC_HYPOTHETICAL)
        self.assertEqual(obs.provenance, "locate_anything")
        self.assertEqual(obs.location, {"frame": "camera", "x": 1.2, "y": 0.4})
        self.assertEqual(obs.modality, "grounding")

    def test_grounding_uncertainty_from_confidence(self) -> None:
        g = _GroundingObs(confidence=0.55)
        obs = observation_from_grounding(g)
        self.assertAlmostEqual(obs.uncertainty, 0.45)


class FusionTest(unittest.TestCase):
    def test_independent_observations_increase_confidence_but_never_certainty(self) -> None:
        a = make_observation(
            source="cam1", modality="vision", entity_candidate="vano",
            confidence=0.91, provenance="cam1:frame:1",
        )
        b = make_observation(
            source="mic1", modality="audio", entity_candidate="vano",
            confidence=0.94, provenance="mic1:seg:2",
        )
        fused = fuse_observations(a, b)
        self.assertIsNotNone(fused)
        assert fused is not None
        self.assertGreater(fused.confidence, 0.94)
        self.assertLess(fused.confidence, 1.0)
        self.assertLess(fused.uncertainty, min(a.uncertainty, b.uncertainty))
        # Fusion is an honest epistemic status, not a silent OBSERVED upgrade.
        self.assertEqual(fused.epistemic_status, "FUSED")
        self.assertIn("cam1:frame:1", fused.provenance)
        self.assertIn("mic1:seg:2", fused.provenance)

    def test_conflicting_entity_candidates_do_not_fuse(self) -> None:
        a = make_observation(
            source="cam1", modality="vision", entity_candidate="vano",
            confidence=0.96, provenance="cam1:frame:1",
        )
        b = make_observation(
            source="mic1", modality="audio", entity_candidate="unknown",
            confidence=0.72, provenance="mic1:seg:2",
        )
        self.assertIsNone(fuse_observations(a, b))

    def test_same_provenance_is_not_independent_evidence(self) -> None:
        a = make_observation(
            source="cam1", modality="vision", entity_candidate="vano",
            confidence=0.9, provenance="cam1:frame:1",
        )
        dup = make_observation(
            source="cam1", modality="vision", entity_candidate="vano",
            confidence=0.9, provenance="cam1:frame:1",
        )
        self.assertIsNone(fuse_observations(a, dup))

    def test_low_confidence_observations_do_not_jump(self) -> None:
        a = make_observation(
            source="cam1", modality="vision", entity_candidate="x",
            confidence=0.4, provenance="p1",
        )
        b = make_observation(
            source="cam2", modality="vision", entity_candidate="x",
            confidence=0.45, provenance="p2",
        )
        fused = fuse_observations(a, b)
        self.assertIsNotNone(fused)
        assert fused is not None
        self.assertLess(fused.confidence, 0.75)


if __name__ == "__main__":
    unittest.main()
