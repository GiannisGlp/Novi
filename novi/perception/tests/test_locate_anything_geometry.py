"""Tests: LocateAnything coordinate conversion + geometry validation
(plan Step 2.2/2.3/4 — docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md).

Rules under test:
- source coordinates are integer-normalized to [0, 1000] (NVIDIA output contract);
- inverted / zero-area / out-of-range / non-integer source boxes are rejected;
- pixel conversion is floor/ceil-clamped so every valid source box maps to a
  positive integer pixel box (Novi's Detection convention: (x, y, w, h));
- points convert with rounding + clamping.
"""

from __future__ import annotations

import pytest

from novi.perception.locate_anything_geometry import (
    source_box_to_pixel_box,
    source_point_to_pixel,
    validate_source_box,
    validate_source_point,
)

W, H = 640, 480


class TestValidateSourceBox:
    def test_valid_box_accepted(self):
        validate_source_box(100, 200, 900, 800)  # must not raise

    def test_full_frame_accepted(self):
        validate_source_box(0, 0, 1000, 1000)

    def test_inverted_x_rejected(self):
        with pytest.raises(ValueError, match="x1"):
            validate_source_box(900, 100, 100, 800)

    def test_inverted_y_rejected(self):
        with pytest.raises(ValueError, match="y1"):
            validate_source_box(100, 800, 900, 100)

    def test_zero_area_box_rejected(self):
        with pytest.raises(ValueError, match="area"):
            validate_source_box(100, 100, 100, 200)

    def test_negative_coordinate_rejected(self):
        with pytest.raises(ValueError, match="0.*1000"):
            validate_source_box(-1, 0, 500, 500)

    def test_coordinate_above_1000_rejected(self):
        with pytest.raises(ValueError, match="0.*1000"):
            validate_source_box(0, 0, 1001, 500)

    def test_non_integer_coordinate_rejected(self):
        with pytest.raises(ValueError, match="integer"):
            validate_source_box(10.5, 0, 500, 500)

    def test_bool_coordinate_rejected(self):
        with pytest.raises(ValueError, match="integer"):
            validate_source_box(True, 0, 500, 500)


class TestValidateSourcePoint:
    def test_valid_point_accepted(self):
        validate_source_point(500, 500)

    def test_negative_point_rejected(self):
        with pytest.raises(ValueError):
            validate_source_point(-1, 500)

    def test_point_above_1000_rejected(self):
        with pytest.raises(ValueError):
            validate_source_point(500, 1001)

    def test_non_integer_point_rejected(self):
        with pytest.raises(ValueError):
            validate_source_point(0.5, 500)


class TestSourceBoxToPixelBox:
    def test_basic_conversion(self):
        # (100,200)-(900,800) of [0,1000] on 640x480
        assert source_box_to_pixel_box(100, 200, 900, 800, W, H) == (64, 96, 512, 288)

    def test_full_frame_maps_to_full_image(self):
        assert source_box_to_pixel_box(0, 0, 1000, 1000, W, H) == (0, 0, 640, 480)

    def test_edge_box_clamped_inside_image(self):
        x, y, w, h = source_box_to_pixel_box(999, 999, 1000, 1000, W, H)
        assert x + w <= W and y + h <= H
        assert x >= 0 and y >= 0

    def test_tiny_box_yields_positive_pixel_area(self):
        x, y, w, h = source_box_to_pixel_box(0, 0, 1, 1, W, H)
        assert w >= 1 and h >= 1

    def test_zero_or_negative_image_dims_rejected(self):
        with pytest.raises(ValueError, match="dimension"):
            source_box_to_pixel_box(0, 0, 100, 100, 0, 480)
        with pytest.raises(ValueError, match="dimension"):
            source_box_to_pixel_box(0, 0, 100, 100, 640, -1)


class TestSourcePointToPixel:
    def test_center_point(self):
        assert source_point_to_pixel(500, 500, W, H) == (320, 240)

    def test_origin_point(self):
        assert source_point_to_pixel(0, 0, W, H) == (0, 0)

    def test_max_point_clamped_to_last_pixel(self):
        assert source_point_to_pixel(1000, 1000, W, H) == (639, 479)

    def test_subpixel_point_rounds_to_nearest_pixel(self):
        # 1/1000 * 640 = 0.64 -> 1 ; 1/1000 * 480 = 0.48 -> 0
        assert source_point_to_pixel(1, 1, W, H) == (1, 0)
