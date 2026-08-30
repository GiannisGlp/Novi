# Novi Training Datasets

Canonical example format: `docs/plans/01_BRAIN/23_NOVI_LEARNING_AND_TRAINING_PLAN.md` §5
(situation → decision → response). Every example must pass
`training.schemas.validate_example` and `training.collection.validator.validate_example_ctx`
before it may enter a `curated/` set. See `training/README.md` for ground rules.

## Layout

```text
datasets/
├── raw/           exported traces before sanitization (never committed, short-lived)
├── cleaned/       sanitized + schema-valid examples (intermediate)
├── curated/       human-reviewed, validated seed + grown corpora  <-- source of truth
├── sft/           SFT-ready sets (converted from curated at train time)
├── dpo/           preference pairs (plan §11/§33)
├── retrieval/     retrieval ranking records (plan §13/§34)
├── grounding/     grounding records (plan §14)
└── evaluation/    held-out benchmark splits
```

Directories are created on demand by the collection pipeline
(`training/collection/validator.run_collection_pipeline`) and by
`build_seed.py`. Git tracks only curated content and the generator.

## Versioning

- Every dataset carries a version suffix (`_v1`, `_v2`, …).
- `curated/memory_index_vN.json` lists every memory id referenced by that
  version — dataset-level validation rejects dangling memory references.
- `build_seed.py` is deterministic (fixed templates + seeded RNG): the
  committed `seed_dialogue_v1.jsonl` must be reproducible byte-for-byte
  (`python training/datasets/build_seed.py --check`; guarded by tests).

## Current corpus

| Set | Version | Examples | Tasks |
|---|---|---|---|
| `curated/seed_dialogue_v1.jsonl` | v1 | 70 | all 9 SFT task types (plan §10.1) |

The seed is the reviewable starter core (plan §32: first experiment targets
500–2,000 curated examples). It grows through the collection pipeline:
interaction traces → eligibility filter → sanitizer → validation → dedup →
human annotation (plan §6–§9).
