"""LocateAnything source-coordinate geometry: validation + pixel conversion.

NVIDIA LocateAnything emits integer-normalized coordinates in [0, 1000].
Novi's canonical internal box is an integer pixel-space (x, y, w, h) — the
same convention as `Detection`.

Rules (plan Step 2.2/2.3/4, spec 02 §4):
- source boxes must be integers within [0, 1000], strictly ordered
  (x1 < x2, y1 < y2) — inverted and zero-area boxes are rejected;
- pixel conversion uses floor(x1), ceil(x2) so every valid source box maps to
  a positive-area pixel box; bounds are clamped to the image;
- source coordinates are never mutated: the original normalized values are
  preserved by the caller for provenance (see grounding.GroundingObservation).

Pure module: no imports outside stdlib; safe for CI on any platform.
"""

from __future__ import annotations

import math

SOURCE_MAX = 1000


def _require_int(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, got {value!r}")


def _require_dimensions(width: object, height: object) -> None:
    for name, value in (("width", width), ("height", height)):
        _require_int(value, name)
        if value <= 0:  # type: ignore[operator]
            raise ValueError(f"image {name} must be a positive integer dimension, got {value}")


def validate_source_box(x1: int, y1: int, x2: int, y2: int) -> None:
    """Reject non-integer, out-of-range, inverted, or zero-area source boxes."""
    for name, value in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
        _require_int(value, name)
    for name, value in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
        if not 0 <= value <= SOURCE_MAX:
            raise ValueError(f"{name} must be within [0, {SOURCE_MAX}], got {value}")
    if x1 >= x2:
        raise ValueError(f"x1 must be < x2 (inverted or zero-area), got x1={x1}, x2={x2}")
    if y1 >= y2:
        raise ValueError(f"y1 must be < y2 (inverted or zero-area), got y1={y1}, y2={y2}")


def validate_source_point(x: int, y: int) -> None:
    """Reject non-integer or out-of-range source points."""
    for name, value in (("x", x), ("y", y)):
        _require_int(value, name)
    for name, value in (("x", x), ("y", y)):
        if not 0 <= value <= SOURCE_MAX:
            raise ValueError(f"{name} must be within [0, {SOURCE_MAX}], got {value}")


def source_box_to_pixel_box(
    x1: int, y1: int, x2: int, y2: int, width: int, height: int
) -> tuple[int, int, int, int]:
    """Convert a validated [0,1000] source box to pixel (x, y, w, h).

    floor/ceil guarantee a positive-area pixel box for any valid source box;
    the result is clamped so x + w <= width and y + h <= height.
    """
    validate_source_box(x1, y1, x2, y2)
    _require_dimensions(width, height)
    px1 = math.floor(x1 * width / SOURCE_MAX)
    py1 = math.floor(y1 * height / SOURCE_MAX)
    px2 = min(math.ceil(x2 * width / SOURCE_MAX), width)
    py2 = min(math.ceil(y2 * height / SOURCE_MAX), height)
    return (px1, py1, px2 - px1, py2 - py1)


def source_point_to_pixel(x: int, y: int, width: int, height: int) -> tuple[int, int]:
    """Convert a validated [0,1000] source point to a clamped pixel (x, y)."""
    validate_source_point(x, y)
    _require_dimensions(width, height)
    px = min(round(x * width / SOURCE_MAX), width - 1)
    py = min(round(y * height / SOURCE_MAX), height - 1)
    return (px, py)
