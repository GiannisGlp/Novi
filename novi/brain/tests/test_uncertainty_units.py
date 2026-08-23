"""Tests for the uncertainty-and-units work in the spatial model and fusion engine.

Applies the uncertainty-and-units skill:
  - units are attached at input (``_m`` / ``_rad`` suffixes) and stripped at output;
  - uncertainty is propagated through the distance measurement model (GUM
    linearization) and through the fusion confidence model (sample std-dev);
  - results are sanity-checked for dimensional consistency and magnitude.
"""

import unittest

from novi.brain.fusion import ModalityObservation, MultimodalFusion
from novi.brain.spatial_map import Pose2D, convert_distance_m

T = "2026-08-20T12:00:00Z"


def obs(modality, entity, value, conf, recv=T):
    return ModalityObservation(
        modality=modality,
        entity=entity,
        value=value,
        confidence=conf,
        captured_at=recv,
        received_at=recv,
        source=modality,
    )


class Pose2DUncertaintyTest(unittest.TestCase):
    def test_distance_without_uncertainty(self) -> None:
        d, u = Pose2D(0.0, 0.0).distance_to(Pose2D(3.0, 4.0))
        self.assertAlmostEqual(d, 5.0, places=6)
        self.assertEqual(u, 0.0)

    def test_distance_propagates_uncertainty_gum(self) -> None:
        # dx=3, dy=4, dist=5; c_x=0.6, c_y=0.8; each coord unc 0.1.
        # u = sqrt(2*(0.6*0.1)^2 + 2*(0.8*0.1)^2) = sqrt(0.02) ~ 0.1414.
        a = Pose2D(0.0, 0.0, x_unc_m=0.1, y_unc_m=0.1)
        b = Pose2D(3.0, 4.0, x_unc_m=0.1, y_unc_m=0.1)
        d, u = a.distance_to(b)
        self.assertAlmostEqual(d, 5.0, places=6)
        self.assertAlmostEqual(u, 0.02**0.5, places=6)

    def test_distance_uncertainty_scales_with_coordinate_uncertainty(self) -> None:
        a = Pose2D(0.0, 0.0, x_unc_m=0.2, y_unc_m=0.2)
        b = Pose2D(3.0, 4.0, x_unc_m=0.2, y_unc_m=0.2)
        _, u = a.distance_to(b)
        # Doubling input uncertainty doubles the propagated uncertainty.
        self.assertAlmostEqual(u, 2 * (0.02**0.5), places=6)

    def test_zero_distance_returns_zero_uncertainty(self) -> None:
        a = Pose2D(1.0, 1.0, x_unc_m=0.5, y_unc_m=0.5)
        d, u = a.distance_to(Pose2D(1.0, 1.0))
        self.assertEqual(d, 0.0)
        self.assertEqual(u, 0.0)

    def test_snapshot_includes_uncertainty(self) -> None:
        snap = Pose2D(1.0, 2.0, x_unc_m=0.1, y_unc_m=0.2, heading_unc_rad=0.3).snapshot()
        self.assertEqual(snap["x_unc_m"], 0.1)
        self.assertEqual(snap["y_unc_m"], 0.2)
        self.assertEqual(snap["heading_unc_rad"], 0.3)


class UnitConversionTest(unittest.TestCase):
    def test_metres_to_centimetres(self) -> None:
        self.assertAlmostEqual(convert_distance_m(1.0, "cm"), 100.0, places=6)

    def test_metres_to_millimetres(self) -> None:
        self.assertAlmostEqual(convert_distance_m(0.5, "mm"), 500.0, places=6)

    def test_metres_to_metres_identity(self) -> None:
        self.assertAlmostEqual(convert_distance_m(2.5, "m"), 2.5, places=6)

    def test_invalid_unit_raises(self) -> None:
        with self.assertRaises(ValueError):
            convert_distance_m(1.0, "seconds")


class FusionUncertaintyTest(unittest.TestCase):
    def test_single_source_has_zero_uncertainty(self) -> None:
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "lamp", "present", 0.7)])
        self.assertEqual(events[0].confidence_uncertainty, 0.0)

    def test_identical_sources_have_zero_uncertainty(self) -> None:
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "alice", "present", 0.6), obs("speech", "alice", "present", 0.6)])
        self.assertEqual(events[0].confidence_uncertainty, 0.0)

    def test_spread_sources_have_positive_uncertainty(self) -> None:
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "alice", "present", 0.5), obs("speech", "alice", "present", 0.9)])
        # mean 0.7, sample var = ((0.5-0.7)^2 + (0.9-0.7)^2)/1 = 0.08, std ~ 0.2828.
        self.assertAlmostEqual(events[0].confidence_uncertainty, 0.08**0.5, places=6)

    def test_snapshot_includes_uncertainty(self) -> None:
        f = MultimodalFusion()
        events = f.ingest([obs("vision", "alice", "present", 0.5), obs("speech", "alice", "present", 0.9)])
        self.assertIn("confidence_uncertainty", events[0].snapshot())


if __name__ == "__main__":
    unittest.main()
