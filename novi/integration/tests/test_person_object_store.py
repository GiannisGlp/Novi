"""Tests: PersonObjectAssociationStore — durable person↔object co-occurrence memory.

Novi must remember WHAT it has seen a person with, WHERE, and HOW OFTEN:

- note() persists a (person, object, place) co-occurrence row, coalescing
  repeats (count++, last-seen advances) so continuous camera observation
  cannot grow the table unboundedly;
- the same person+object in a different place opens a second row;
- objects_with(person) returns aggregated, deduplicated top objects for that
  person across places, ranked by count then recency;
- seen_with(person, object) aggregates across places into one verdict;
- recent_summary() renders bounded human lines for dialogue grounding
  ("blue mug in kitchen (3x)");
- rename_person() merges rows from an old ref into a new one (naming loop);
- privacy: writes are person-keyed, so note() is refused while the privacy
  switch is off (fail-closed, audited); reads still work.
"""

from __future__ import annotations

import pytest

from novi.integration.person_object_store import PersonObjectAssociationStore


def _tmp(tmp_path) -> PersonObjectAssociationStore:
    return PersonObjectAssociationStore(tmp_path / "association.db")


def _note(store: PersonObjectAssociationStore, **kw):
    kw.setdefault("provenance", {"source": "recognition"})
    return store.note(**kw)


class TestNoteCoalescing:
    def test_note_records_first_seen_and_count(self, tmp_path):
        store = _tmp(tmp_path)
        a = _note(store, person_ref="person-vano", object_ref="object-mug",
                  label="mug", category="cup", place="kitchen", frame_id="f0")
        assert a.person_ref == "person-vano"
        assert a.object_ref == "object-mug"
        assert a.saw_count == 1 and a.place == "kitchen"

    def test_repeat_note_increments_count_without_growing_table(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", category="cup", place="kitchen", frame_id="f0")
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", category="cup", place="kitchen", frame_id="f1")
        rows = store.all(person_ref="person-vano")
        assert len(rows) == 1, "same (person, object, place) must coalesce"
        assert rows[0].saw_count == 2

    def test_distinct_place_is_a_separate_row(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", place="kitchen")
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", place="living-room")
        rows = store.all(person_ref="person-vano")
        assert len(rows) == 2
        assert {r.place for r in rows} == {"kitchen", "living-room"}

    def test_requires_provenance(self, tmp_path):
        store = _tmp(tmp_path)
        with pytest.raises(ValueError):
            store.note(person_ref="person-vano", object_ref="object-mug")


class TestObjectsWith:
    def test_aggregates_objects_across_places_deduped(self, tmp_path):
        store = _tmp(tmp_path)
        # mug seen twice in kitchen + once elsewhere
        for _ in range(2):
            _note(store, person_ref="person-vano", object_ref="object-mug",
                  label="mug", place="kitchen")
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", place="living-room")
        _note(store, person_ref="person-vano", object_ref="object-book",
              label="book", place="kitchen")
        objs = store.objects_with("person-vano")
        # mug (3) before book (1)
        assert [o.object_ref for o in objs] == ["object-mug", "object-book"]
        mug = objs[0]
        assert mug.saw_count == 3 and mug.last_seen_at
        # per-object aggregation dedupes places via the places list
        assert mug.places and set(mug.places) >= {"kitchen", "living-room"}

    def test_empty_for_person_never_seen(self, tmp_path):
        store = _tmp(tmp_path)
        assert store.objects_with("person-nobody") == []

    def test_limit(self, tmp_path):
        store = _tmp(tmp_path)
        for i in range(5):
            _note(store, person_ref="person-vano",
                  object_ref=f"object-o{i}", label=f"o{i}", place="kitchen")
        assert len(store.objects_with("person-vano", limit=2)) == 2


class TestSeenWith:
    def test_none_when_never_seen(self, tmp_path):
        store = _tmp(tmp_path)
        assert store.seen_with("person-vano", "object-mug") is None

    def test_returns_count_last_seen_and_places(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", place="kitchen", last_seen_at="2026-01-01T00:00:00.000Z")
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", place="living-room", last_seen_at="2026-01-02T00:00:00.000Z")
        verdict = store.seen_with("person-vano", "object-mug")
        assert verdict is not None and verdict["seen"] is True
        assert verdict["count"] == 2
        assert set(verdict["places"]) == {"kitchen", "living-room"}
        assert verdict["last_seen_at"] == "2026-01-02T00:00:00.000Z"


class TestRecentSummary:
    def test_renders_human_lines(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", category="cup", place="kitchen")
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", category="cup", place="kitchen")
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", category="cup", place="kitchen")
        summary = store.recent_summary("person-vano", limit=3)
        assert any("mug" in s and "kitchen" in s and "(3x)" in s for s in summary)

    def test_bounded(self, tmp_path):
        store = _tmp(tmp_path)
        for i in range(6):
            _note(store, person_ref="person-vano",
                  object_ref=f"object-o{i}", label=f"o{i}", place=f"room{i}")
        assert len(store.recent_summary("person-vano", limit=2)) <= 2


class TestRenamePerson:
    def test_merges_rows_into_new_ref_summing_counts(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-new-person-1", object_ref="object-mug",
              label="mug", place="kitchen")
        _note(store, person_ref="person-new-person-1", object_ref="object-mug",
              label="mug", place="kitchen")
        _note(store, person_ref="person-new-person-1", object_ref="object-book",
              label="book", place="kitchen")
        moved = store.rename_person("person-new-person-1", "person-vano")
        assert moved == 2
        assert store.all(person_ref="person-new-person-1") == []
        rows = store.all(person_ref="person-vano")
        by_obj = {r.object_ref: r for r in rows}
        assert by_obj["object-mug"].saw_count == 2, "counts merge, not overwrite"

    def test_merge_min_first_max_last(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-x", object_ref="object-mug",
              label="mug", place="kitchen",
              first_seen_at="2026-01-01T00:00:00.000Z",
              last_seen_at="2026-01-03T00:00:00.000Z", count_incr=3)
        _note(store, person_ref="person-vano", object_ref="object-mug",
              label="mug", place="kitchen",
              first_seen_at="2026-01-02T00:00:00.000Z",
              last_seen_at="2026-01-04T00:00:00.000Z", count_incr=2)
        store.rename_person("person-x", "person-vano")
        row = store.all(person_ref="person-vano")[0]
        assert row.saw_count == 5
        assert row.first_seen_at == "2026-01-01T00:00:00.000Z"
        assert row.last_seen_at == "2026-01-04T00:00:00.000Z"

    def test_noop_when_same_ref(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-vano", object_ref="object-mug", place="kitchen")
        assert store.rename_person("person-vano", "person-vano") == 0
        assert len(store.all(person_ref="person-vano")) == 1


class TestPrivacy:
    def test_note_refused_when_privacy_off(self, tmp_path):
        store = _tmp(tmp_path)
        store.set_privacy(False, reason="user asked")
        with pytest.raises(PermissionError):
            _note(store, person_ref="person-vano", object_ref="object-mug", place="kitchen")

    def test_write_refuses_without_auditing_as_allowed(self, tmp_path):
        store = _tmp(tmp_path)
        store.set_privacy(False, reason="test")
        assert store.privacy_enabled is False
        with pytest.raises(PermissionError):
            _note(store, person_ref="person-vano", object_ref="object-mug", place="kitchen")

    def test_reads_available_when_privacy_off(self, tmp_path):
        store = _tmp(tmp_path)
        _note(store, person_ref="person-vano", object_ref="object-mug", place="kitchen")
        store.set_privacy(False, reason="test")
        assert len(store.objects_with("person-vano")) == 1

    def test_re_enable_allows_writes(self, tmp_path):
        store = _tmp(tmp_path)
        store.set_privacy(False, reason="test")
        store.set_privacy(True, reason="test")
        a = _note(store, person_ref="person-vano", object_ref="object-mug", place="kitchen")
        assert a.saw_count == 1
