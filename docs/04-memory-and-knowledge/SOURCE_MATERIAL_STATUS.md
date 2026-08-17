# 04 — Memory and Knowledge Source Material Status Registry

**Status:** CANONICAL SOURCE DISPOSITION REGISTRY — V1.1
**Date:** 2026-08-17

This registry defines how Memory and Knowledge documents are treated. `CANONICAL` means current normative authority. `MERGE` identifies material incorporated into a canonical destination. `MOVE` identifies implementation material belonging elsewhere. `REFERENCE` identifies research/background material. `HISTORICAL` identifies preserved non-normative material. `GAP` identifies a source number for which no repository file was found.

## Current normative spine

The only active semantic architecture authority is the `01`–`18` canonical set listed in `ARCHITECTURE_INDEX.md`.

## Transitional 95–106 disposition

The former 95–106 transitional authorities have been moved to:

`archive/transitional-95-106/`

They are preserved unchanged for provenance and recovery, but are **NON-NORMATIVE**. Their semantic authority has been consolidated into 01–18.

## Historical 00–94

The existing historical 00–94 corpus was reviewed source-by-source during consolidation. Existing files are preserved under `archive/` and are **NON-NORMATIVE**.

For every existing source, useful normative requirements were mapped into canonical destinations or identified as belonging to system architecture. No historical source is required as an active semantic authority.

## Source inventory gaps

The following numeric source identifiers are not present in the repository inventory examined during consolidation:

| Identifier | Status | Decision |
|---|---|---|
| `24` | GAP | No source file found; do not invent one |
| `65` | GAP | No source file found; do not invent one |

These are inventory gaps, not missing canonical architecture documents.

## Infrastructure boundary

The following are not semantic Memory & Knowledge implementation authority:

- physical storage/schema mechanics;
- transaction implementation;
- replication transport;
- recovery implementation;
- vector/FTS implementation;
- runtime scheduling;
- observability implementation.

Their semantic requirements may be referenced from Memory & Knowledge, while implementation authority belongs to the appropriate system architecture.

## Supersession rule

Historical files are preserved because they provide architectural provenance and research traceability. They do not override 01–18. Any future archival deletion requires an explicit repository-level decision and must not be inferred from semantic consolidation alone.

## V1.1 status

```text
00–94 existing sources       REVIEWED / DISPOSITIONED
24                           GAP
65                           GAP
95–106                       TRANSITIONAL / ARCHIVED
01–18                        CURRENT CANONICAL AUTHORITY
```
