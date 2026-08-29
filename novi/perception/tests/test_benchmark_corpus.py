"""Tests: benchmark corpus loader/validation (plan Step 10.1/10.2).

Loads the real versioned corpus (docs/07-locate-anything/benchmark/corpus-v1.json)
and verifies fail-fast validation on malformed records.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from novi.perception.benchmark_corpus import BenchmarkCorpus, sha256_file

REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS_V1 = REPO_ROOT / "docs" / "07-locate-anything" / "benchmark" / "corpus-v1.json"


class TestRealCorpus:
    def test_v1_loads_with_all_records(self):
        corpus = BenchmarkCorpus.load(CORPUS_V1)
        assert corpus.corpus_id == "novi-la-corpus"
        assert corpus.version == "1"
        assert len(corpus.records) == 6

    def test_record_ids_unique_and_negatives_marked(self):
        corpus = BenchmarkCorpus.load(CORPUS_V1)
        ids = [r.record_id for r in corpus.records]
        assert len(ids) == len(set(ids))
        negatives = [r for r in corpus.records if r.is_negative]
        assert [r.record_id for r in negatives] == ["rec-person-negative", "rec-unicorn-negative"]

    def test_ground_truth_boxes_are_valid_normalized(self):
        corpus = BenchmarkCorpus.load(CORPUS_V1)
        for r in corpus.records:
            for gt in r.expected_boxes:
                x1, y1, x2, y2 = gt.box
                assert 0 <= x1 < x2 <= 1000
                assert 0 <= y1 < y2 <= 1000

    def test_image_sha_matches_file(self):
        corpus = BenchmarkCorpus.load(CORPUS_V1)
        expected = sha256_file(REPO_ROOT / "novi" / "assets" / "test-image.png")
        assert all(r.image_sha256 == expected for r in corpus.records)

    def test_provenance_fields_present(self):
        corpus = BenchmarkCorpus.load(CORPUS_V1)
        for r in corpus.records:
            assert r.source != "unknown"
            assert r.license != "unknown"
            assert r.category


class TestValidation:
    def test_duplicate_record_id_rejected(self):
        with pytest.raises(ValueError, match="duplicate"):
            BenchmarkCorpus.from_dict(
                {
                    "corpus_id": "c",
                    "version": "1",
                    "records": [
                        {"record_id": "a", "query": "q", "image_path": "p", "image_sha256": "0" * 64, "image_width": 10, "image_height": 10, "expected_no_object": True},
                        {"record_id": "a", "query": "q", "image_path": "p", "image_sha256": "0" * 64, "image_width": 10, "image_height": 10, "expected_no_object": True},
                    ],
                }
            )

    def test_no_object_conflicts_with_boxes_rejected(self):
        with pytest.raises(ValueError, match="conflicts"):
            BenchmarkCorpus.from_dict(
                {
                    "corpus_id": "c",
                    "version": "1",
                    "records": [
                        {
                            "record_id": "a",
                            "query": "q",
                            "image_path": "p",
                            "image_sha256": "0" * 64,
                            "image_width": 10,
                            "image_height": 10,
                            "expected_no_object": True,
                            "expected_boxes": [{"label": "x", "box": [0, 0, 10, 10]}],
                        }
                    ],
                }
            )

    def test_bad_sha_rejected(self):
        with pytest.raises(ValueError, match="sha256"):
            BenchmarkCorpus.from_dict(
                {
                    "corpus_id": "c",
                    "version": "1",
                    "records": [
                        {"record_id": "a", "query": "q", "image_path": "p", "image_sha256": "zz", "image_width": 10, "image_height": 10, "expected_no_object": True},
                    ],
                }
            )

    def test_empty_corpus_rejected(self):
        with pytest.raises(ValueError, match="at least one"):
            BenchmarkCorpus.from_dict({"corpus_id": "c", "version": "1", "records": []})

    def test_missing_query_rejected(self):
        with pytest.raises(ValueError, match="query"):
            BenchmarkCorpus.from_dict(
                {
                    "corpus_id": "c",
                    "version": "1",
                    "records": [
                        {"record_id": "a", "query": " ", "image_path": "p", "image_sha256": "0" * 64, "image_width": 10, "image_height": 10, "expected_no_object": True},
                    ],
                }
            )

    def test_out_of_range_gt_box_rejected(self):
        with pytest.raises(ValueError, match="1000"):
            BenchmarkCorpus.from_dict(
                {
                    "corpus_id": "c",
                    "version": "1",
                    "records": [
                        {
                            "record_id": "a",
                            "query": "q",
                            "image_path": "p",
                            "image_sha256": "0" * 64,
                            "image_width": 10,
                            "image_height": 10,
                            "expected_boxes": [{"label": "x", "box": [0, 0, 1001, 10]}],
                        }
                    ],
                }
            )
