"""Tests: tracking-lite — IoU association, hysteresis, lost tracks (doc 02 §1.2).

- same object across consecutive frames keeps one track id;
- first/last_seen + hit/miss counters feed world-state last_seen decay;
- hysteresis: a track needs min_hits before it is "confirmed" and survives
  a couple of missed frames before it is "lost" (no flicker at threshold);
- label change on an associated track is rejected (identity is stable).
"""

from __future__ import annotations

import pytest

from novi.perception.detection import Detection
from novi.perception.tracking import ObjectTracker


def _det(label: str, x: int, y: int, conf: float = 0.9, frame_id: str = "f1") -> Detection:
    return Detection(label=label, confidence=conf, bbox=(x, y, 80, 120), frame_id=frame_id)


class TestAssociation:
    def test_same_object_across_frames_keeps_one_track(self):
        t = ObjectTracker()
        t.update([_det("cup", 100, 100)], frame_id="f1")
        active = t.update([_det("cup", 104, 102)], frame_id="f2")
        assert len(active) == 1
        assert t.track_count == 1

    def test_first_last_seen_and_hits(self):
        t = ObjectTracker()
        tr = t.update([_det("cup", 100, 100)], frame_id="f1")[0]
        assert (tr.first_frame_id, tr.last_frame_id) == ("f1", "f1")
        tr2 = t.update([_det("cup", 104, 102)], frame_id="f2")[0]
        assert tr2.track_id == tr.track_id
        assert (tr2.first_frame_id, tr2.last_frame_id) == ("f1", "f2")
        assert tr2.hits == 2

    def test_two_distinct_objects_two_tracks(self):
        t = ObjectTracker()
        t.update([_det("cup", 100, 100), _det("book", 400, 300)], frame_id="f1")
        assert t.track_count == 2


class TestHysteresis:
    def test_unconfirmed_until_min_hits(self):
        t = ObjectTracker(min_hits=3)
        tr = t.update([_det("cup", 100, 100)], frame_id="f1")[0]
        assert tr.confirmed is False
        t.update([_det("cup", 102, 101)], frame_id="f2")
        trs = t.update([_det("cup", 103, 103)], frame_id="f3")
        assert trs[0].confirmed is True

    def test_misses_below_max_age_still_tracked_then_lost(self):
        t = ObjectTracker(max_age_frames=2)
        tr = t.update([_det("cup", 100, 100)], frame_id="f1")[0]
        t.update([], frame_id="f2")  # miss 1: still alive
        assert any(x.track_id == tr.track_id for x in t.all_tracks)
        t.update([], frame_id="f3")  # miss 2: expired
        assert not any(x.track_id == tr.track_id for x in t.all_tracks)
        lost = t.lost_tracks
        assert len(lost) == 1 and lost[0].track_id == tr.track_id

    def test_reappearing_object_gets_new_track_after_expiry(self):
        t = ObjectTracker(max_age_frames=1)
        tr = t.update([_det("cup", 100, 100)], frame_id="f1")[0]
        t.update([], frame_id="f2")  # one miss expires (misses >= max_age)
        assert not any(x.track_id == tr.track_id for x in t.all_tracks)
        fresh = t.update([_det("cup", 100, 100)], frame_id="f3")[0]
        assert fresh.track_id != tr.track_id


class TestLabelStability:
    def test_label_change_on_associated_track_raises(self):
        t = ObjectTracker()
        t.update([_det("cup", 100, 100)], frame_id="f1")
        with pytest.raises(ValueError):
            t.update([_det("book", 102, 101)], frame_id="f2")


class TestSnapshot:
    def test_world_state_snapshot_shape(self):
        t = ObjectTracker()
        t.update([_det("cup", 100, 100)], frame_id="f1")
        snap = t.snapshot()
        assert snap["track_count"] == 1
        entry = snap["tracks"][0]
        assert {"track_id", "label", "bbox", "first_frame_id", "last_frame_id", "hits", "misses", "confirmed"} <= set(entry)
