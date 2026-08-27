import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.privacy import PrivacyGovernance
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.g = PrivacyGovernance()

    def test_credential_keyword(self):
        c = self.g.classify(memory_type="utterance", content="my password is hunter2")
        self.assertEqual(c.privacy_class, "credential")

    def test_person_utterance_is_personal(self):
        c = self.g.classify(memory_type="utterance", content="alice said hello", entity_refs=("alice",), modality="speech")
        self.assertEqual(c.privacy_class, "personal")

    def test_location_keyword(self):
        c = self.g.classify(memory_type="perception", content={"label": "gps coordinates 12.3,4.5"})
        self.assertEqual(c.privacy_class, "location")

    def test_derived_type(self):
        c = self.g.classify(memory_type="summary", content="a summary")
        self.assertEqual(c.privacy_class, "derived")

    def test_default_operational(self):
        c = self.g.classify(memory_type="perception", content={"label": "door"})
        self.assertEqual(c.privacy_class, "operational")

    def test_retention(self):
        self.assertIsNone(self.g.retention_seconds_for("public"))
        self.assertIsNotNone(self.g.retention_seconds_for("personal"))
        self.assertIsNotNone(self.g.expiry_for("credential"))


class GovernanceStoreTests(unittest.TestCase):
    def _store(self, td):
        return DurableMemoryStore(Path(td) / "p.db")

    def test_classify_and_govern_record(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            g = PrivacyGovernance(store)
            adm = store.admit(memory_type="utterance", content="alice said hello", confidence=0.9, verification_status="verified", privacy_class="personal", provenance={"source": "s"}, entity_refs=("alice",))
            self.assertTrue(adm.accepted)
            g.govern(adm.memory_id, privacy_class="personal")
            state = store.records_by_entity("alice")[0]
            self.assertEqual(state["purpose"], "general")
            self.assertIsNotNone(state["expires_at"])
            store.close()

    def test_erase_propagates_to_dependents(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            g = PrivacyGovernance(store)
            base = store.admit(memory_type="perception", content={"label": "alice"}, confidence=0.9, verification_status="verified", privacy_class="personal", provenance={"source": "s"}, entity_refs=("alice",))
            dep = store.admit(memory_type="summary", content="derived about alice", confidence=0.7, verification_status="verified", privacy_class="derived", provenance={"source": "s"}, dependency_refs=(base.memory_id,), entity_refs=("alice",))
            self.assertTrue(dep.accepted)
            self.assertEqual(store.dependent_ids(base.memory_id), (dep.memory_id,))
            report = g.erase_memory(base.memory_id)
            self.assertIn(base.memory_id, report.erased_ids)
            self.assertIn(dep.memory_id, report.propagated)
            # both physically removed -> cannot be resurrected by recovery
            self.assertIsNone(store.get_state(base.memory_id))
            self.assertIsNone(store.get_state(dep.memory_id))
            store.close()

    def test_forget_entity_right_to_be_forgotten(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            g = PrivacyGovernance(store)
            store.admit(memory_type="utterance", content="alice visited", confidence=0.9, verification_status="verified", privacy_class="personal", provenance={"source": "s"}, entity_refs=("alice",))
            store.admit(memory_type="perception", content={"label": "door"}, confidence=0.6, verification_status="verified", privacy_class="operational", provenance={"source": "s"}, entity_refs=("door",))
            report = g.forget_entity("alice")
            self.assertEqual(len(report.erased_ids), 1)
            self.assertEqual(store.active_count, 1)  # only the door record remains
            store.close()

    def test_authorize_ids_gate(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            g = PrivacyGovernance(store)
            pub = store.admit(memory_type="perception", content={"label": "door"}, confidence=0.6, verification_status="verified", privacy_class="public", provenance={"source": "s"})
            sens = store.admit(memory_type="utterance", content="medical condition", confidence=0.8, verification_status="verified", privacy_class="sensitive", provenance={"source": "s"})
            allowed = g.authorize_ids([pub.memory_id, sens.memory_id], requested_purpose="general", max_sensitivity="personal")
            self.assertIn(pub.memory_id, allowed)
            self.assertNotIn(sens.memory_id, allowed)
            store.close()

    def test_sweep_expires_by_retention(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            g = PrivacyGovernance(store, retention_seconds={"credential": 1})
            m = store.admit(memory_type="memory", content="password hunter2", confidence=0.9, verification_status="verified", privacy_class="credential", provenance={"source": "s"})
            g.govern(m.memory_id, privacy_class="credential")
            past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            store.set_expiry(m.memory_id, past)
            self.assertEqual(store.expired_ids(datetime.now(timezone.utc).isoformat()), (m.memory_id,))
            report = g.sweep()
            self.assertIn(m.memory_id, report.erased_ids)
            store.close()

    def test_restrict_and_generalize(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            g = PrivacyGovernance(store)
            adm = store.admit(memory_type="utterance", content="alice is at the kitchen", confidence=0.8, verification_status="verified", privacy_class="personal", provenance={"source": "s"}, entity_refs=("alice",))
            self.assertTrue(g.restrict(adm.memory_id, purpose="social"))
            self.assertEqual(store.get_state(adm.memory_id), "restricted")
            self.assertTrue(g.generalize(adm.memory_id))
            state = store.get_state(adm.memory_id)
            self.assertIsNotNone(state)
            store.close()


class BrainPrivacyTests(unittest.TestCase):
    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("person", 0.8, (0, 0, 1, 1)),)

    def _brain(self, db=None):
        return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(self.PersonBackend()), store_path=db, config=MacBrainConfig(curiosity_enabled=False))

    def test_utterance_classified_and_governed(self):
        from novi.brain.models.stt import TranscriptionResult
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "b.db")
            b = self._brain(db)
            b.start()
            b.ingest_transcript(TranscriptionResult(text="my password is hunter2", language="en", confidence=0.9, audio_path="", provider="t", model_id="t"))
            counts = b.governance.snapshot()["counts_by_privacy_class"]
            b.stop()
            self.assertIn("credential", counts)

    def test_forget_entity_removes_records(self):
        from novi.brain.models.stt import TranscriptionResult
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "b.db")
            b = self._brain(db)
            b.start()
            b.ingest_transcript(TranscriptionResult(text="alice visited today", language="en", confidence=0.9, audio_path="", provider="t", model_id="t"))
            before = b.governance.snapshot()["total_active"]
            res = b.forget_entity("alice")
            b.stop()
            self.assertGreaterEqual(before, 1)
            self.assertGreaterEqual(len(res["erased"]), 1)
            self.assertIn("privacy.entity_erased", [e["event_type"] for e in b.events])

    def test_privacy_status(self):
        with tempfile.TemporaryDirectory() as td:
            b = self._brain(str(Path(td) / "b.db"))
            b.start()
            status = b.privacy_status()
            b.stop()
            self.assertTrue(status["enabled"])
            self.assertIn("counts_by_privacy_class", status)


if __name__ == "__main__":
    unittest.main()
