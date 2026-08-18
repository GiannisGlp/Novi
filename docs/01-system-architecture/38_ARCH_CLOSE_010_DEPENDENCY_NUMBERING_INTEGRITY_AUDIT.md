# 38 — ARCH-CLOSE-010 Dependency and Numbering Integrity Audit

**Status:** AUDIT COMPLETE — corrective actions identified
**Priority:** P0
**Authority:** System Architecture
**Closure item:** ARCH-CLOSE-010
**Audit date:** 2026-08-18

## 1. Purpose

Verify that architecture references resolve to current documents, that semantic authority is unambiguous, that historical numbering is not mistaken for authority, and that duplicate filenames/number prefixes do not create competing definitions.

The governing rule is that the exact document path/title and explicit authority status determine authority; numeric prefixes are organizational labels and are not semantic identifiers.

## 2. Audit result

The repository is **semantically consistent enough to continue**, but the audit found **legacy numbering collisions and stale status text** that must be governed before System Architecture can be declared fully closed.

No evidence was found that these numbering collisions create a second semantic authority for the same contract. They are documentation-integrity issues, not architectural ownership conflicts.

## 3. Authority hierarchy confirmed

The current System Architecture README defines the authority chain as:

```text
Novi North Star
      ↓
Project strategy
      ↓
System architecture
      ↓
Domain architecture
      ↓
Technology ADRs
      ↓
Implementation specifications
      ↓
Validation evidence
```

It also states that newer explicitly approved ADRs or higher-authority documents resolve conflicts and that implementation may not silently resolve architectural conflicts.

The canonical contract baseline further states that serialization, transport and storage implementations do not become semantic authorities merely because they implement a contract.

Therefore:

```text
semantic authority ≠ filename number
semantic authority ≠ schema format
semantic authority ≠ database
semantic authority ≠ model
```

## 4. Canonical contract authority

`16_CANONICAL_SYSTEM_CONTRACTS.md` is the semantic authority for the cross-domain contract set.

`17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` governs implementation/schema rules.

`24_ARCHITECTURE_CONTRACT_OWNERSHIP_RECONCILIATION.md` records ownership reconciliation.

`25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md` records executable validation evidence.

The machine-readable registry and schemas are implementation artifacts subordinate to the semantic authority.

## 5. Numbering collisions found

Several architecture documents use the same numeric prefix for different semantic documents. Examples confirmed in the current repository include:

| Prefix | Document A | Document B | Semantic conflict? | Action |
|---|---|---|---|---|
| 17 | `17_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md` | `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` | No | Exact path/title is authoritative; update indexes if needed |
| 18 | `18_NVIDIA_PLATFORM_VALIDATION_MATRIX.md` | `18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md` | No | Keep distinct semantic roles; avoid numeric-only references |
| 19 | `19_EXECUTABLE_ARCHITECTURE_TEST_STRATEGY.md` | `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md` | No | Use exact filenames / closure IDs |
| 20 | `20_DEPLOYMENT_MANIFEST_SPECIFICATION.md` | `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md` | No | Use exact filenames / closure IDs |
| 21 | `21_ARCHITECTURE_COMPLETION_GATE.md` | `21_RUNTIME_RESOURCE_BUDGETS_AND_DETERMINISTIC_EXECUTION.md` | No | Use exact filenames / closure IDs |
| 22 | `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md` | `22_RUNTIME_VERSION_COMPATIBILITY_AND_LIFECYCLE.md` | No | Closure register must reference exact path |

These are **legacy organizational numbering collisions**, not duplicate semantic authorities.

## 6. Numbering policy decision

Numeric prefixes are now explicitly treated as **non-authoritative organizational labels**.

The canonical identity of an architecture artifact is:

```text
repository path
+
exact filename
+
semantic title
+
explicit authority/status
+
closure ID where applicable
```

Future cross-references MUST use the exact filename or a stable `ARCH-CLOSE-*` identifier. References such as "document 18" are prohibited when more than one document has that prefix.

This resolves the ambiguity without performing a large-scale rename that could introduce more stale references.

## 7. Closure-ID policy

P0 closure workstreams use stable IDs:

```text
ARCH-CLOSE-001 Canonical contracts
ARCH-CLOSE-002 Consistency mapping
ARCH-CLOSE-003 Durable storage
ARCH-CLOSE-004 Runtime/version tuple
ARCH-CLOSE-005 Safety integration
ARCH-CLOSE-006 Time synchronization
ARCH-CLOSE-007 Resource budgets
ARCH-CLOSE-008 Deployment manifest
ARCH-CLOSE-009 Architecture-to-test mapping
ARCH-CLOSE-010 Dependency/numbering integrity
```

These IDs are the preferred references for closure status.

## 8. Historical references

The architecture domain contains historical files whose names include older identifiers such as `06_107`, `07_108`, `08_110` and `09_111`.

These identifiers are retained because they identify the historical/domain architecture lineage, but they must not be interpreted as current sequential document numbers.

The current authority is determined by the exact path, title, status and authority declaration.

The architecture README already describes these files as durable/distributed system foundations and identifies their semantic roles.

## 9. Storage references

`18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md` exists and remains **PROPOSED — NOT YET ADOPTED**.

`27_ARCH_CLOSE_003_STAGE_1_STORAGE_BENCHMARK_SPEC.md` defines the empirical benchmark and fault-injection gate.

No stale reference to a nonexistent Stage-1 storage ADR is permitted in current closure documentation.

The important semantic distinction remains:

```text
SQLite = Stage-1 candidate
RocksDB/PostgreSQL = alternatives
benchmark + fault injection = adoption gate
```

## 10. Time references

The current normative time architecture is `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`.

It defines wall/system time, monotonic time, ROS time, simulation time, hardware/sensor time, timestamp provenance, synchronization status, uncertainty, stale data, action validity and replay semantics.

`ARCH-CLOSE-006` remains the implementation/evidence closure identifier. A missing implementation-gate file must not be confused with absence of the underlying normative time architecture.

## 11. Runtime/version references

`29_ARCH_CLOSE_004_RUNTIME_VERSION_COMPATIBILITY_TUPLE.md` is the explicit closure artifact for reproducibility of the Stage-1 runtime.

`22_RUNTIME_VERSION_COMPATIBILITY_AND_LIFECYCLE.md` is the broader normative compatibility/lifecycle architecture.

The two documents have different roles:

```text
22 = general runtime/version architecture
29 = ARCH-CLOSE-004 closure-specific implementation gate
```

Neither is a competing semantic authority.

## 12. Deployment references

`20_DEPLOYMENT_MANIFEST_SPECIFICATION.md` is the broader deployment-manifest architecture.

`36_ARCH_CLOSE_008_DEPLOYMENT_MANIFEST.md` is the closure-specific implementation contract.

These are complementary rather than competing authorities.

## 13. Test/validation references

`19_EXECUTABLE_ARCHITECTURE_TEST_STRATEGY.md` defines the general validation strategy.

`37_ARCH_CLOSE_009_ARCHITECTURE_TO_TEST_MAPPING.md` defines the P0 closure-specific requirement/test/evidence matrix.

`25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md` records actual contract-validation evidence.

`10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md` defines the evidence hierarchy and traceability rules.

These documents form a layered validation model rather than duplicate authorities.

## 14. Hardware numbering collision

The hardware domain contains both:

- `24_GNSS_GPS_AND_GLOBAL_POSITIONING.md`
- `24_HARDWARE_SELECTION_AND_BOM_BASELINE.md`

This is a cross-domain numbering collision, not a semantic collision. Their scopes are different:

```text
GNSS document
    → global-positioning architecture

Hardware BOM document
    → component-selection/BOM framework
```

The collision must be removed or explicitly governed by the hardware-domain index before the final global documentation audit.

## 15. Sensor architecture status

`33_NOVI_SENSOR_AND_PERCEPTION_ARCHITECTURE.md` is the current sensing requirements baseline.

It deliberately keeps component selection open while defining the required sensing envelope, including:

- multiple RGB cameras;
- multiple RGB-D cameras;
- 3D LiDAR;
- GNSS/GPS and optional RTK;
- IMU with gyroscope and accelerometer;
- wheel encoders;
- thermal camera;
- microphone array;
- speakers;
- proximity/contact/cliff sensing;
- hardware-health telemetry.

The final sensor BOM remains a later evidence-based hardware decision.

## 16. Compute-platform references

`32_COMPUTE_PLATFORM_COMPARISON_AGX_ORIN_64_VS_THOR.md` is the current hardware research baseline.

It explicitly keeps the final compute choice open and distinguishes:

```text
AGX Orin 64GB → mobile candidate
Thor T5000    → stationary/heavy-compute candidate
Thor mobile   → conditional option requiring energy/thermal evidence
```

This is consistent with the hardware architecture principle that physical hardware is replaceable behind stable interfaces.

## 17. Dependency integrity findings

The following dependency patterns are valid and intentionally layered:

```text
16 Canonical Contracts
        ↓
17 Contract Implementation Standard
        ↓
contract registry / schemas
        ↓
validation evidence
```

```text
107–111 durable/distributed architecture
        ↓
18 Stage-1 Storage ADR
        ↓
27 Storage Benchmark Gate
```

```text
19 Time Architecture
        ↓
ARCH-CLOSE-006 implementation/evidence
```

```text
22 Runtime Compatibility Architecture
        ↓
29 ARCH-CLOSE-004
```

```text
20 Deployment Manifest Architecture
        ↓
36 ARCH-CLOSE-008
```

```text
19 Executable Test Strategy
        ↓
37 ARCH-CLOSE-009
```

These relationships do not introduce circular semantic ownership.

## 18. Required corrective actions

### A — Exact-path references

All new architecture documents MUST reference exact filenames or closure IDs, never bare numeric document numbers.

### B — Hardware numbering

Resolve the `24_` collision in the Hardware domain during the next hardware documentation synchronization pass.

### C — Legacy audit refresh

`15_ARCHITECTURE_FILE_AUDIT.md` predates the current closure campaign and should be refreshed after the closure set is stable.

### D — Index synchronization

The System Architecture README and master documentation index should list all current P0 closure artifacts explicitly.

### E — Final stale-reference scan

Before Architecture is marked `COMPLETE`, perform an automated repository-wide scan that fails on:

- references to nonexistent files;
- bare ambiguous numeric references;
- references to superseded authority without an explicit compatibility note;
- duplicate semantic authority claims;
- closure IDs with inconsistent status.

## 19. ARCH-CLOSE-010 decision

**ARCH-CLOSE-010: NOT YET CLOSED.**

The semantic dependency audit is complete and the numbering ambiguity has been formally governed, but corrective actions A–E remain before a strict full-integrity closure can be claimed.

This is intentional. The repository should not claim a clean audit while the hardware numbering collision and automated stale-reference scan remain outstanding.

## 20. Architectural invariant

> **Every architecture dependency must resolve to an identifiable current authority, and no document number, filename, implementation artifact or historical reference may silently become a competing semantic authority.**
