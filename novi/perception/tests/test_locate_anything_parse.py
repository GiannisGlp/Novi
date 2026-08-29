"""Tests: strict LocateAnything output parser (plan Step 2.1/2.2/2.4).

Case list from Step 2.4: one box, many boxes, one point, many points, none,
duplicate labels, punctuation in labels, malformed tokens, truncated
responses, out-of-range coordinates, inverted boxes, mixed valid/invalid
blocks, empty response — plus strictness rules from Step 2.2 (non-integer
coordinates, missing tokens, impossible nesting, excessive result counts,
malformed category separators).

Acceptance: malformed output is never converted into a valid world
observation — invalid blocks are never silently repaired.
"""

from __future__ import annotations

import pytest

from novi.perception.locate_anything_parse import parse_locate_anything_output


class TestBoxes:
    def test_one_box(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>100 200 900 800</box>")
        assert out.valid
        assert len(out.boxes) == 1
        b = out.boxes[0]
        assert (b.label, b.x1, b.y1, b.x2, b.y2) == ("cup", 100, 200, 900, 800)
        assert out.points == ()

    def test_special_token_coordinates_accepted(self):
        # The released model renders each coordinate as a special token
        # `<N>` (plan Step 2.1 notation `<box><x1><y1><x2><y2></box>`).
        out = parse_locate_anything_output("<ref>the person</ref><box><4><207><20><231></box>")
        assert out.valid
        assert (out.boxes[0].x1, out.boxes[0].y1, out.boxes[0].x2, out.boxes[0].y2) == (4, 207, 20, 231)

    def test_mixed_plain_and_special_token_coordinates(self):
        out = parse_locate_anything_output("<ref>cup</ref><box><100> 200 <900> 800</box>")
        assert out.valid
        assert (out.boxes[0].x1, out.boxes[0].y1, out.boxes[0].x2, out.boxes[0].y2) == (100, 200, 900, 800)

    def test_many_boxes_keep_order(self):
        out = parse_locate_anything_output(
            "<ref>cup</ref><box>0 0 100 100</box>"
            "<ref>book</ref><box>200 200 300 300</box>"
            "<ref>laptop</ref><box>400 400 500 500</box>"
        )
        assert out.valid
        assert [b.label for b in out.boxes] == ["cup", "book", "laptop"]

    def test_punctuation_in_label_preserved(self):
        out = parse_locate_anything_output("<ref>blue cup, with handle</ref><box>10 10 90 90</box>")
        assert out.valid
        assert out.boxes[0].label == "blue cup, with handle"

    def test_duplicate_labels_are_all_kept(self):
        out = parse_locate_anything_output(
            "<ref>cup</ref><box>0 0 100 100</box><ref>cup</ref><box>300 300 400 400</box>"
        )
        assert out.valid
        assert len(out.boxes) == 2
        assert out.boxes[0].x1 == 0 and out.boxes[1].x1 == 300

    def test_bounds_zero_and_1000_accepted(self):
        out = parse_locate_anything_output("<ref>wall</ref><box>0 0 1000 1000</box>")
        assert out.valid
        assert out.boxes[0].x2 == 1000


class TestPoints:
    def test_one_point(self):
        out = parse_locate_anything_output("<ref>handle</ref><box>500 500</box>")
        assert out.valid
        assert len(out.points) == 1
        assert (out.points[0].label, out.points[0].x, out.points[0].y) == ("handle", 500, 500)
        assert out.boxes == ()

    def test_special_token_point_coordinates(self):
        out = parse_locate_anything_output("<ref>handle</ref><box><500><500></box>")
        assert out.valid
        assert (out.points[0].x, out.points[0].y) == (500, 500)

    def test_many_points(self):
        out = parse_locate_anything_output(
            "<ref>a</ref><box>1 1</box><ref>b</ref><box>2 2</box><ref>c</ref><box>3 3</box>"
        )
        assert out.valid
        assert [(p.x, p.y) for p in out.points] == [(1, 1), (2, 2), (3, 3)]


class TestNone:
    def test_none_marker(self):
        out = parse_locate_anything_output("<box>none</box>")
        assert out.valid
        assert out.none_seen
        assert out.boxes == () and out.points == ()

    def test_capitalized_none_marker_accepted(self):
        # The released model renders the no-object marker as "None".
        out = parse_locate_anything_output("<ref>the person</ref><box>None</box>")
        assert out.valid
        assert out.none_seen
        assert out.boxes == () and out.points == ()

    def test_mixed_valid_blocks(self):
        out = parse_locate_anything_output(
            "<ref>cup</ref><box>100 200 300 400</box>"
            "<ref>handle</ref><box>250 300</box>"
            "<box>none</box>"
        )
        assert out.valid
        assert len(out.boxes) == 1 and len(out.points) == 1 and out.none_seen


class TestStrictRejections:
    def test_inverted_box_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>900 200 100 800</box>")
        assert not out.valid
        assert out.boxes == ()
        assert any("x1" in e or "inverted" in e for e in out.errors)

    def test_zero_area_box_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>100 100 100 200</box>")
        assert not out.valid
        assert out.boxes == ()

    def test_out_of_range_coordinate_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>0 0 1001 800</box>")
        assert not out.valid
        assert out.boxes == ()

    def test_non_integer_coordinate_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>10.5 200 300 400</box>")
        assert not out.valid

    def test_comma_separator_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>100,200 300 400</box>")
        assert not out.valid

    def test_missing_ref_close_rejected(self):
        out = parse_locate_anything_output("<ref>cup<box>100 200 300 400</box>")
        assert not out.valid
        assert any("ref" in e for e in out.errors)

    def test_missing_box_close_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>100 200 300 400")
        assert not out.valid
        assert any("box" in e for e in out.errors)

    def test_box_without_ref_rejected(self):
        out = parse_locate_anything_output("<box>100 200 300 400</box>")
        assert not out.valid
        assert any("ref" in e for e in out.errors)

    def test_impossible_nesting_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box><ref>cup</ref>100 200 300 400</box>")
        assert not out.valid

    def test_stray_text_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref> garbage <box>100 200 300 400</box>")
        assert not out.valid

    def test_empty_label_rejected(self):
        out = parse_locate_anything_output("<ref></ref><box>100 200 300 400</box>")
        assert not out.valid

    def test_truncated_coordinates_rejected(self):
        out = parse_locate_anything_output("<ref>cup</ref><box>100 200 300</box>")
        assert not out.valid

    def test_excessive_result_count_truncated_with_error(self):
        out = parse_locate_anything_output(
            "<ref>a</ref><box>0 0 1 1</box><ref>b</ref><box>0 0 1 1</box><ref>c</ref><box>0 0 1 1</box>",
            max_results=2,
        )
        assert not out.valid
        assert len(out.boxes) == 2
        assert any("max_results" in e for e in out.errors)


class TestEmpty:
    def test_empty_response_is_valid_empty(self):
        out = parse_locate_anything_output("")
        assert out.valid
        assert out.boxes == () and out.points == () and not out.none_seen

    def test_whitespace_only_response_is_valid_empty(self):
        out = parse_locate_anything_output("   \n\t ")
        assert out.valid
