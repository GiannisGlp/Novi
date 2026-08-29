"""Strict parser for LocateAnything structured output (plan Step 2.1/2.2).

NVIDIA's released worker represents grounding as special tokens:

    <ref>label</ref><box><x1><y1><x2><y2></box>   box (integer [0,1000] corners)
    <box><x><y></box>                             point
    <box>none</box>                               no object

Rules (Step 2.2) — never permissive, never silently repair:
- non-integer, out-of-range ([0,1000]), inverted, and zero-area boxes are
  rejected (validated via locate_anything_geometry);
- missing/mismatched tokens, impossible nesting, stray text, empty labels,
  and malformed separators are recorded as errors;
- a 4-int box without a preceding `<ref>` is rejected (missing token);
- a bare 2-int `<box>` is a label-less point; `<box>none</box>` needs no ref;
- excessive result counts truncate with an error.

Block isolation: valid blocks are still parsed for audit, but any error makes
the outcome invalid — the caller must treat the whole response as untrusted
(GroundingResult becomes success=False, fail-closed).

Pure stdlib module: safe to import and test anywhere, including CI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from novi.perception.locate_anything_geometry import (
    validate_source_box,
    validate_source_point,
)

REF_OPEN, REF_CLOSE = "<ref>", "</ref>"
BOX_OPEN, BOX_CLOSE = "<box>", "</box>"
_INT = re.compile(r"-?\d+")
_STOP_TOKENS = (REF_OPEN, BOX_OPEN)


@dataclass(frozen=True)
class ParsedBox:
    label: str
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass(frozen=True)
class ParsedPoint:
    label: str
    x: int
    y: int


@dataclass(frozen=True)
class ParseOutcome:
    boxes: tuple[ParsedBox, ...]
    points: tuple[ParsedPoint, ...]
    none_seen: bool
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def _skip_junk(text: str, pos: int, limit: int) -> int:
    """Advance to the next `<ref>`/`<box>` token (strict recovery, no repair)."""
    best = limit
    for tok in _STOP_TOKENS:
        hit = text.find(tok, pos)
        if hit != -1 and hit < best:
            best = hit
    return best


def _coords_ok(parts: list[str], errors: list[str]) -> bool:
    for part in parts:
        if not _INT.fullmatch(part):
            errors.append(f"non-integer coordinate token: {part!r}")
            return False
    return True


_COORD_TOKEN = re.compile(r"<(-?\d{1,4})>")


def _split_coord_parts(content: str) -> list[str]:
    """Tokenize `<box>` content into coordinate parts.

    The released model renders each coordinate as a special token `<N>`
    (plan Step 2.1 notation `<box><x1><y1><x2><y2></box>`), sometimes with
    whitespace between them. This converts both plain integers and `<N>`
    renderings into plain integer text — the strict numeric validation
    below still applies to every part. Non-coordinate `<...>` fragments
    (e.g. nesting) survive as-is and fail validation.
    """
    parts: list[str] = []
    for piece in content.split():
        pos = 0
        while pos < len(piece):
            m = _COORD_TOKEN.match(piece, pos)
            if m:
                parts.append(m.group(1))
                pos = m.end()
                continue
            if piece[pos] == "<":
                end = piece.find(">", pos + 1)
                end = len(piece) if end == -1 else end + 1
            else:
                end = piece.find("<", pos)
                end = len(piece) if end == -1 else end
            seg = piece[pos:end]
            if seg:
                parts.append(seg)
            pos = end
    return parts


def parse_locate_anything_output(text: str, *, max_results: int = 50) -> ParseOutcome:
    """Parse raw model text into typed boxes/points; never repair malformed input."""
    if max_results < 1:
        raise ValueError(f"max_results must be >= 1, got {max_results}")

    boxes: list[ParsedBox] = []
    points: list[ParsedPoint] = []
    errors: list[str] = []
    none_seen = False
    pending_label: str | None = None

    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break

        if text.startswith(REF_OPEN, i):
            end = text.find(REF_CLOSE, i + len(REF_OPEN))
            if end == -1:
                errors.append("missing </ref>")
                i = _skip_junk(text, i + len(REF_OPEN), n)
                continue
            label = text[i + len(REF_OPEN) : end].strip()
            if not label:
                errors.append("empty <ref> label")
                pending_label = None
            else:
                pending_label = label
            i = end + len(REF_CLOSE)
            j = i
            while j < n and text[j].isspace():
                j += 1
            if not text.startswith(BOX_OPEN, j):
                errors.append("expected <box> after </ref>")
                pending_label = None
                i = _skip_junk(text, i, n)
            else:
                i = j
            continue

        if text.startswith(BOX_OPEN, i):
            end = text.find(BOX_CLOSE, i + len(BOX_OPEN))
            if end == -1:
                errors.append("missing </box>")
                i = _skip_junk(text, i + len(BOX_OPEN), n)
                pending_label = None
                continue
            content = text[i + len(BOX_OPEN) : end].strip()
            i = end + len(BOX_CLOSE)

            if content.lower() == "none":
                none_seen = True
                pending_label = None
                continue

            parts = _split_coord_parts(content)
            label = pending_label or ""
            pending_label = None

            if len(parts) == 4:
                if not label:
                    errors.append("expected <ref> before box coordinates")
                    continue
                if not _coords_ok(parts, errors):
                    continue
                x1, y1, x2, y2 = (int(p) for p in parts)
                try:
                    validate_source_box(x1, y1, x2, y2)
                except ValueError as exc:
                    errors.append(str(exc))
                    continue
                if len(boxes) + len(points) >= max_results:
                    errors.append(f"exceeded max_results={max_results}")
                    break
                boxes.append(ParsedBox(label=label, x1=x1, y1=y1, x2=x2, y2=y2))
            elif len(parts) == 2:
                if not _coords_ok(parts, errors):
                    continue
                x, y = (int(p) for p in parts)
                try:
                    validate_source_point(x, y)
                except ValueError as exc:
                    errors.append(str(exc))
                    continue
                if len(boxes) + len(points) >= max_results:
                    errors.append(f"exceeded max_results={max_results}")
                    break
                points.append(ParsedPoint(label=label, x=x, y=y))
            else:
                errors.append(f"malformed box content (expected 2 or 4 integers, or 'none'): {content!r}")
            continue

        if text.startswith(REF_CLOSE, i) or text.startswith(BOX_CLOSE, i):
            errors.append("unexpected closing token")
            i += len(REF_CLOSE if text.startswith(REF_CLOSE, i) else BOX_CLOSE)
            continue

        errors.append(f"unexpected text at offset {i}: {text[i:i+20]!r}")
        i = _skip_junk(text, i + 1, n)

    return ParseOutcome(
        boxes=tuple(boxes),
        points=tuple(points),
        none_seen=none_seen,
        errors=tuple(errors),
    )
