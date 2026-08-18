# 29 — ARCH-CLOSE-004 Runtime / Version Compatibility Tuple

**Status:** Defined — implementation pinning pending  
**Priority:** P0  
**Authority:** System Architecture  
**Scope:** Reproducible Stage-1 Novi runtime

## 1. Purpose

Define the minimum version identity required to reproduce, validate and diagnose a Novi runtime.

## 2. Compatibility tuple

Every validated Novi runtime must identify:

```text
OS
Python/runtime
compiler/toolchain
SQLite
SQLite build options
ML framework
model runtime
ROS 2 profile (when enabled)
simulator (when enabled)
database/schema migration version
Novi revision
contract registry revision
model identifiers/hashes
```

The tuple is an immutable provenance artifact for each release/build candidate.

## 3. Stage-1 baseline

Stage-1 is Mac-first and local/offline. The exact macOS and Python versions are to be pinned by the implementation environment rather than inferred from documentation.

SQLite is currently defined as the Stage-1 durable-state candidate in document 28, with the exact tested release/build recorded at runtime. The official SQLite release page currently identifies 3.53.3 (2026-06-26) as the latest release, but Novi must not silently track future releases. urlSQLite release informationhttps://sqlite.org/index.html?lang=en

## 4. Version identity requirements

A component version is incomplete unless the runtime can distinguish:

- declared version;
- actual loaded version;
- build identity where relevant;
- configuration/compile options;
- architecture/platform;
- Novi compatibility status.

## 5. Runtime validation

Startup validation must reject or explicitly quarantine incompatible tuples before authoritative state transitions begin.

Validation must cover:

- contract registry compatibility;
- database migration compatibility;
- SQLite version/build compatibility;
- model/runtime compatibility;
- hardware profile compatibility where applicable;
- configuration schema compatibility.

## 6. Reproducibility

A deployment artifact must allow a reviewer to reconstruct the compatibility tuple from repository revision and runtime diagnostics without relying on memory or manual notes.

## 7. Evidence gate

ARCH-CLOSE-004 closes only after at least one reproducible Stage-1 runtime has:

1. a machine-readable tuple;
2. startup validation;
3. pinned component versions;
4. CI or equivalent verification;
5. documented upgrade procedure;
6. evidence that incompatible versions are rejected or explicitly handled.

## 8. Non-goal

This document does not select production versions for every future component. It defines the mechanism by which those decisions become reproducible and auditable.
