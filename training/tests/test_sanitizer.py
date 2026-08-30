"""Tests for the training-data sanitizer (plan 23 §7–§8)."""

from __future__ import annotations

import json
from pathlib import Path

from training.collection.sanitizer import (
    REDACTED,
    ConsentState,
    RetentionPolicy,
    SanitizationReport,
    Sanitizer,
)


def _example(person_id: str = "person:vano", response: str = "Got it.") -> dict:
    return {
        "example_id": "dlg-0001",
        "task": "natural_dialogue",
        "situation": {
            "person": {"id": person_id, "name": "Vano", "relationship": "owner", "confidence": 0.98},
            "world": {}, "conversation": {}, "memory": [], "social": {},
        },
        "decision": {"dialogue_act": "RESPOND", "reason": "", "verbosity": "short"},
        "response": response,
    }


class TestRedaction:
    def test_redacts_email(self):
        s = Sanitizer()
        ex = _example(response="Write to vano@example.com about it.")
        out, _ = s.sanitize(ex)
        assert "vano@example.com" not in out["response"]
        assert REDACTED in out["response"]

    def test_redacts_phone_number(self):
        s = Sanitizer()
        ex = _example(response="Call me at +1 (555) 123-4567 soon.")
        out, _ = s.sanitize(ex)
        assert "555" not in out["response"]

    def test_redacts_credentials(self):
        s = Sanitizer()
        ex = _example(response="The api key is sk-abc123def456 and password hunter2.")
        out, _ = s.sanitize(ex)
        assert "sk-abc123def456" not in out["response"]
        assert "hunter2" not in out["response"]

    def test_plain_text_untouched(self):
        s = Sanitizer()
        text = "Yeah, that makes sense."
        out, _ = s.sanitize(_example(response=text))
        assert out["response"] == text


class TestPersonAbstraction:
    def test_raw_name_abstracted_to_owner(self):
        s = Sanitizer()
        out, _ = s.sanitize(_example(person_id="vano"))
        assert out["situation"]["person"]["id"] == "person:owner_001"

    def test_unknown_person_gets_anon_id(self):
        s = Sanitizer()
        out, _ = s.sanitize(_example(person_id="alice"))
        assert out["situation"]["person"]["id"] == "person:anon_001"

    def test_abstract_ids_stable_across_calls(self):
        s = Sanitizer()
        a, _ = s.sanitize(_example(person_id="alice"))
        b, _ = s.sanitize(_example(person_id="alice"))
        assert a["situation"]["person"]["id"] == b["situation"]["person"]["id"]

    def test_biometric_refs_stripped_from_world(self):
        s = Sanitizer()
        ex = _example()
        ex["situation"]["world"] = {"voiceprint_ref": "voiceprint:embed-9", "location": "office"}
        out, _ = s.sanitize(ex)
        assert "voiceprint_ref" not in out["situation"]["world"]


class TestBiometricBlocking:
    def test_biometric_content_dropped_from_language_training(self):
        s = Sanitizer()
        ex = _example(response="I matched her face embedding against the gallery.")
        out, report = s.sanitize(ex)
        assert out is None
        assert report.dropped_biometric == 1


class TestConsent:
    def test_no_consent_dropped(self):
        s = Sanitizer(consent=ConsentState(consenting={"person:owner_001"}))
        out, report = s.sanitize(_example(person_id="person:vano"))
        assert out is None
        assert report.dropped_no_consent == 1

    def test_consenting_kept(self):
        s = Sanitizer(consent=ConsentState(consenting={"person:vano"}))
        out, report = s.sanitize(_example(person_id="person:vano"))
        assert out is not None
        assert report.kept == 1


class TestRetention:
    def test_expired_example_dropped(self):
        s = Sanitizer(retention=RetentionPolicy(max_age_days=30))
        ex = _example()
        ex["example_id"] = "old-1"
        ex["_exported_at"] = "2020-01-01T00:00:00+00:00"
        out, report = s.sanitize(ex)
        assert out is None
        assert report.dropped_expired == 1

    def test_fresh_example_kept(self):
        s = Sanitizer(retention=RetentionPolicy(max_age_days=30))
        out, report = s.sanitize(_example())
        assert out is not None
        assert report.dropped_expired == 0


class TestDatasetDeletion:
    def test_purge_removes_dataset_files(self, tmp_path: Path):
        (tmp_path / "curated").mkdir()
        f = tmp_path / "curated" / "seed.jsonl"
        f.write_text(json.dumps(_example()) + "\n")
        s = Sanitizer()
        removed = s.purge_dataset(tmp_path / "curated")
        assert removed == 1
        assert not f.exists()

    def test_report_counts_accumulate(self):
        s = Sanitizer()
        out, report = s.sanitize(_example(response="email me at a@b.co"))
        assert report.redacted >= 1
        assert isinstance(report, SanitizationReport)
