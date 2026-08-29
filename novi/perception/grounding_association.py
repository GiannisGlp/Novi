"""Grounding -> tracking association (plan Step 5.4).

Grounding observations are per-frame geometry; ObjectTracker owns temporal
continuity. Association is deliberately conservative:

- box observations associate to the active track with the best IoU above
  `iou_threshold` (track labels and grounding labels are different
  vocabularies, so label equality is NOT required);
- point observations associate to the nearest track centroid within
  `point_dist_threshold_px`;
- anything uncertain becomes a `candidate` observation (track_id=None) —
  a candidate is a proposal for world state, never invented continuity.

Pure stdlib module; fully deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

from novi.perception.grounding import GroundingObservation, GroundingResult, PointObservation
from novi.perception.tracking import Track, _iou


@dataclass
class GroundingAssociation:
    """One grounding observation's relationship to the track table."""

    observation: GroundingObservation | PointObservation
    track_id: int | None  # None => candidate (uncertain), never guessed continuity
    iou: float | None
    status: str  # "associated" | "candidate"


@dataclass
class GroundingOutcome:
    """What ground_frame contributed: the typed result + track associations."""

    frame_id: str
    query: str
    result: GroundingResult
    associations: list[GroundingAssociation]


def _centroid(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    x, y, w, h = bbox
    return (x + w / 2.0, y + h / 2.0)


def _distance(a: tuple[int, int], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def associate_grounding_to_tracks(
    result: GroundingResult,
    active_tracks: list[Track],
    *,
    frame_id: str,
    query: str,
    iou_threshold: float = 0.30,
    point_dist_threshold_px: float = 40.0,
) -> GroundingOutcome:
    """Associate every observation in `result` to the best matching track.

    Uncertain matches become candidates — the plan forbids inventing
    continuity (Step 5.4). Association never mutates tracks.
    """
    associations: list[GroundingAssociation] = []
    for obs in result.observations:
        if isinstance(obs, GroundingObservation):
            best_id, best_iou = None, iou_threshold
            for tr in active_tracks:
                iou = _iou(tr.bbox, obs.pixel_box)
                if iou > best_iou:
                    best_id, best_iou = tr.track_id, iou
            if best_id is not None:
                associations.append(GroundingAssociation(obs, best_id, best_iou, "associated"))
            else:
                associations.append(GroundingAssociation(obs, None, None, "candidate"))
        else:  # PointObservation
            best_id, best_dist = None, point_dist_threshold_px
            for tr in active_tracks:
                d = _distance(obs.pixel_point, _centroid(tr.bbox))
                if d <= best_dist:
                    best_id, best_dist = tr.track_id, d
            if best_id is not None:
                associations.append(GroundingAssociation(obs, best_id, None, "associated"))
            else:
                associations.append(GroundingAssociation(obs, None, None, "candidate"))
    return GroundingOutcome(
        frame_id=frame_id,
        query=query,
        result=result,
        associations=associations,
    )
