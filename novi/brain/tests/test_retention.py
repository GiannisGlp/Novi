"""Phase 4b (north-star gap analysis): retention + capacity eviction
enforced at the store.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 4b:
"Enforce retention + capacity eviction at the store (per-type TTL + size
cap; honor expires_at automatically)."

Acceptance:
- records past their expires_at are automatically excluded from retrieval
  (honor-without-sweep) and tombstoned by the enforcer's sweep;
- per-type TTLs expire stale records (protected types untouched);
- capacity caps evict the lowest-value record, never protected classes.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from novi.brain.retention import RetentionEnforcer, RetentionPolicy, RetentionReport
from novi.brain.storage import DurableMemoryStore


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_days_ago(days: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


class _StoreCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = DurableMemoryStore(str(Path(self._tmp.name) / "mem.db"))

    def tearDown(self) -> None:
        self.store.close()
        self._tmp.cleanup()

    def _admit(self, *, memory_type: str = "note", text: str, confidence: float = 0.9,
               created_at: str = "", expires_at: str | None = None, evarified: str = "verified",
               source: str = "camera.sensor") -> str | None:
        ref = self.store.admit(
            memory_type=memory_type,
            content={"text": text},
            confidence=confidence,
            verification_status=evarified,
            privacy_class="unclassified",
            provenance={"source": source, "source_class": "DIRECT_SENSOR"},
            entity_refs=("cup",),
            created_at=created_at or _iso_now(),
        )
        if expires_at is not None and ref.memory_id:
            self.store.set_expiry(ref.memory_id, expires_at)
        return ref.memory_id


class ExpiryHonoringTests(_StoreCase):
    def test_expired_record_excluded_from_retrieval_automatically(self):
        mid = self._admit(text="stale secret note", expires_at="2020-01-01T00:00:00Z")
        self.assertIsNotNone(mid)
        self.assertEqual(self.store.retrieve("secret", limit=5), ())
        self.assertEqual(self.store.retrieve_indexed("secret", limit=5), ())
        self.assertEqual(self.store.retrieve_ranked("secret", limit=5), ())
        # The record still exists (soft): the enforcer physically tombstones.
        rows = self.store.active_rows()
        self.assertEqual(len(rows), 0, "active_rows must not surface expired records")

    def test_live_record_still_retrievable(self):
        self._admit(text="fresh note", expires_at="2099-01-01T00:00:00Z")
        self.assertEqual(len(self.store.retrieve("fresh", limit=5)), 1)


class EnforcerSweepTests(_StoreCase):
    def test_sweep_tombstones_expired_and_ttl_records(self):
        policy = RetentionPolicy(default_ttl_days=30, max_records=1000, type_ttls={"prediction": 1.0})
        enforcer = RetentionEnforcer(self.store, policy)
        # Directly expired.
        self._admit(memory_type="note", text="expired note", expires_at="2020-01-01T00:00:00Z")
        # Older than its type TTL (1 day).
        self._admit(memory_type="prediction", text="old prediction", created_at=_iso_days_ago(5))
        # Fresh, protected.
        self._admit(memory_type="invariant", text="protected invariant", created_at=_iso_days_ago(400))
        report = enforcer.sweep(now=_iso_now())
        self.assertEqual(len(report.expired_expired), 1)
        self.assertGreaterEqual(len(report.expired_ttl), 1)
        self.assertEqual(len(self.store.active_rows()), 1, "only the protected/fresh record survives")
        survivors = [r["record"].content for r in self.store.active_rows()]
        del survivors

    def test_capacity_eviction_evicts_lowest_value(self):
        policy = RetentionPolicy(max_records=3, protected_types=("invariant",))
        enforcer = RetentionEnforcer(self.store, policy)
        kept_ids = []
        for i in range(4):
            mid = self._admit(
                memory_type="observation",
                text=f"sensor reading {i}",
                confidence=0.9 if i == 3 else 0.3,
                created_at=_iso_now(),
            )
            kept_ids.append(mid)
        report = enforcer.sweep(now=_iso_now())
        self.assertLessEqual(len(self.store.active_rows()), 3)
        # The high-value record survives; a low-value one was evicted.
        surviving = {r["record"].memory_id for r in self.store.active_rows()}
        self.assertIn(kept_ids[3], surviving, "the strongest record must survive capacity eviction")
        self.assertGreaterEqual(len(report.evicted), 1)

    def test_protected_type_never_evicted(self):
        policy = RetentionPolicy(max_records=1, protected_types=("invariant",))
        enforcer = RetentionEnforcer(self.store, policy)
        self._admit(memory_type="invariant", text="safety invariant", created_at=_iso_now())
        for i in range(3):
            self._admit(memory_type="note", text=f"chatter {i}", confidence=0.5, created_at=_iso_now())
        report = enforcer.sweep(now=_iso_now())
        remaining_types = {r["record"].memory_type for r in self.store.active_rows()}
        self.assertIn("invariant", remaining_types)
        self.assertGreaterEqual(len(report.evicted), 1)


class ReportShapeTests(unittest.TestCase):
    def test_report_defaults(self):
        report = RetentionReport()
        self.assertEqual(len(report.expired_expired) + len(report.expired_ttl) + len(report.evicted), 0)
        snap = report.snapshot()
        self.assertIn("expired", snap)
        self.assertIn("evicted", snap)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
