"""Versioned Novi-local grounding benchmark corpus (plan Phase 10, Steps 10.1/10.2).

Each record carries: image (path + sha256 + dims), query, target boxes in
[0,1000]-normalized space, expected identity, category, and
rights/provenance. Ground truth is honest: every box is annotated with a
source + optional caveat note. The corpus lives in JSON
(`docs/07-locate-anything/benchmark/corpus-v1.json`) so it is versioned and
reviewable; this module validates and loads it.

Categories (plan Step 10.1): household objects, robot workspace,
people/hands, clutter, occlusion, similar objects, small objects,
text/signs, novel descriptions, negative queries.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from novi.perception.locate_anything_geometry import validate_source_box

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GroundTruthBox:
    label: str
    box: tuple[int, int, int, int]  # x1, y1, x2, y2 normalized [0,1000]
    note: str | None = None


@dataclass(frozen=True)
class BenchmarkRecord:
    record_id: str
    image_path: str
    image_sha256: str
    image_width: int
    image_height: int
    query: str
    category: str
    source: str
    license: str
    expected_boxes: tuple[GroundTruthBox, ...] = ()
    expected_no_object: bool = False
    notes: str | None = None

    @property
    def is_negative(self) -> bool:
        return self.expected_no_object


@dataclass(frozen=True)
class BenchmarkCorpus:
    corpus_id: str
    version: str
    records: tuple[BenchmarkRecord, ...]

    @classmethod
    def load(cls, path: str | Path) -> "BenchmarkCorpus":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "BenchmarkCorpus":
        corpus_id = raw.get("corpus_id") or ""
        version = str(raw.get("version") or "")
        if not corpus_id or not version:
            raise ValueError("corpus requires corpus_id and version")
        records: list[BenchmarkRecord] = []
        seen: set[str] = set()
        for item in raw.get("records", []):
            record = _record_from_dict(item)
            if record.record_id in seen:
                raise ValueError(f"duplicate record_id {record.record_id!r}")
            seen.add(record.record_id)
            records.append(record)
        if not records:
            raise ValueError("corpus must contain at least one record")
        return cls(corpus_id=corpus_id, version=version, records=tuple(records))


def _record_from_dict(item: dict) -> BenchmarkRecord:
    record_id = item.get("record_id") or ""
    if not record_id:
        raise ValueError("record requires record_id")
    query = item.get("query") or ""
    if not query.strip():
        raise ValueError(f"{record_id}: query must be non-empty")
    category = item.get("category") or "unknown"
    sha = item.get("image_sha256") or ""
    if not _SHA256.match(sha):
        raise ValueError(f"{record_id}: image_sha256 must be 64-hex")
    width, height = int(item["image_width"]), int(item["image_height"])
    if width <= 0 or height <= 0:
        raise ValueError(f"{record_id}: image dims must be positive")

    boxes: list[GroundTruthBox] = []
    for b in item.get("expected_boxes", []):
        label = b.get("label") or ""
        x1, y1, x2, y2 = (int(v) for v in b["box"])
        validate_source_box(x1, y1, x2, y2)
        if not label:
            raise ValueError(f"{record_id}: gt box requires a label")
        boxes.append(GroundTruthBox(label=label, box=(x1, y1, x2, y2), note=b.get("note")))

    no_object = bool(item.get("expected_no_object", False))
    if no_object and boxes:
        raise ValueError(f"{record_id}: expected_no_object conflicts with expected_boxes")
    if not no_object and not boxes:
        raise ValueError(f"{record_id}: record needs expected_boxes or expected_no_object")

    return BenchmarkRecord(
        record_id=record_id,
        image_path=item["image_path"],
        image_sha256=sha,
        image_width=width,
        image_height=height,
        query=query,
        category=category,
        source=item.get("source") or "unknown",
        license=item.get("license") or "unknown",
        expected_boxes=tuple(boxes),
        expected_no_object=no_object,
        notes=item.get("notes"),
    )


def sha256_file(path: str | Path) -> str:
    """Compute the sha256 of an image file (for provenance records)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
