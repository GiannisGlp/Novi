"""Tracking-lite: IoU association + hysteresis (doc 02 §1.2).

No heavy tracker, no re-ID: centroid/IoU association across consecutive
frames keeps world-state `last_seen` coherent. Hysteresis (min_hits to
confirm, max_age_frames to expire) prevents threshold flicker.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from novi.perception.detection import Detection


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    if inter == 0:
        return 0.0
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


@dataclass
class Track:
    track_id: int
    label: str
    bbox: tuple[int, int, int, int]
    first_frame_id: str
    last_frame_id: str
    hits: int = 1
    misses: int = 0
    confirmed: bool = False
    last_confidence: float = 0.0

    def snapshot(self) -> dict:
        return {
            "track_id": self.track_id,
            "label": self.label,
            "bbox": self.bbox,
            "first_frame_id": self.first_frame_id,
            "last_frame_id": self.last_frame_id,
            "hits": self.hits,
            "misses": self.misses,
            "confirmed": self.confirmed,
        }


class ObjectTracker:
    """IoU-greedy association; confirmed/lost lifecycle with hysteresis."""

    def __init__(
        self,
        *,
        iou_threshold: float = 0.30,
        min_hits: int = 2,
        max_age_frames: int = 3,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.min_hits = min_hits
        self.max_age_frames = max_age_frames
        self._tracks: dict[int, Track] = {}
        self._lost: list[Track] = []
        self._ids = itertools.count(1)

    # -- state -----------------------------------------------------------

    @property
    def track_count(self) -> int:
        return len(self._tracks)

    @property
    def all_tracks(self) -> list[Track]:
        return list(self._tracks.values())

    @property
    def lost_tracks(self) -> list[Track]:
        return list(self._lost)

    def snapshot(self) -> dict:
        return {"track_count": len(self._tracks), "tracks": [t.snapshot() for t in self._tracks.values()]}

    # -- update -------------------------------------------------------------

    def update(self, detections: list[Detection], *, frame_id: str) -> list[Track]:
        """Associate detections to tracks; return this frame's active tracks."""
        unmatched_tracks = set(self._tracks)

        for det in detections:
            best_id, best_iou = None, self.iou_threshold
            for tid, tr in self._tracks.items():
                iou = _iou(tr.bbox, det.bbox)
                if tr.label == det.label and iou > best_iou:
                    best_id, best_iou = tid, iou
            if best_id is not None:
                tr = self._apply(best_id, det, frame_id)
                unmatched_tracks.discard(best_id)
            else:
                # identity stability: a different label heavily overlapping an
                # existing track is a label flip, not a new object
                flipped = [
                    tr.label
                    for tr in self._tracks.values()
                    if tr.label != det.label and _iou(tr.bbox, det.bbox) > self.iou_threshold
                ]
                if flipped:
                    raise ValueError(
                        f"label flip {flipped[0]!r} -> {det.label!r} on overlapping track "
                        f"in frame {frame_id}: identity must be stable"
                    )
                tr = self._spawn(det, frame_id)

        # age out un-matched tracks
        for tid in list(unmatched_tracks):
            tr = self._tracks[tid]
            tr.misses += 1
            if tr.misses >= self.max_age_frames:
                del self._tracks[tid]
                self._lost.append(tr)

        return [t for t in self._tracks.values() if t.last_frame_id == frame_id]

    # -- internals -------------------------------------------------------------

    def _apply(self, tid: int, det: Detection, frame_id: str) -> Track:
        tr = self._tracks[tid]
        if det.label != tr.label:
            raise ValueError(
                f"track {tid} label flip {tr.label!r} -> {det.label!r}: identity must be stable"
            )
        tr.bbox = det.bbox
        tr.last_frame_id = frame_id
        tr.hits += 1
        tr.misses = 0
        tr.last_confidence = det.confidence
        if not tr.confirmed and tr.hits >= self.min_hits:
            tr.confirmed = True
        return tr

    def _spawn(self, det: Detection, frame_id: str) -> Track:
        tr = Track(
            track_id=next(self._ids),
            label=det.label,
            bbox=det.bbox,
            first_frame_id=frame_id,
            last_frame_id=frame_id,
            last_confidence=det.confidence,
        )
        if tr.hits >= self.min_hits:
            tr.confirmed = True
        self._tracks[tr.track_id] = tr
        return tr
