# 38 — ARCH-CLOSE-010 Dependency and Numbering Integrity Audit

**Status:** REMEDIATION COMPLETE — final automated verification pending  
**Priority:** P0 / critical / high importance  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-010  
**Audit date:** 2026-08-19

## 1. Purpose

Verify that architecture references resolve to current documents, that semantic authority is unambiguous, that historical numbering is not mistaken for authority, and that duplicate filenames/number prefixes do not create competing definitions.

The governing rule is that the exact document path/title and explicit authority status determine authority; numeric prefixes are organizational labels and are not semantic identifiers.

## 2. Previous audit disposition

The 2026-08-18 audit identified five corrective actions before strict closure:

- A — require exact-path or stable closure-ID references;
- B — resolve the Hardware `24_` numbering collision;
- C — refresh the legacy architecture-file audit;
- D — synchronize the System Architecture README and master index;
- E — run the repository-wide automated stale-reference/integrity scan.

Actions A–D have now been remediated or formally governed. Action E remains the final objective-evidence gate.

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

If two documents appear to conflict, the newer explicitly approved ADR or higher-authority document wins. Implementation must not silently resolve architectural conflicts.

Therefore:

```text
semantic authority ≠ filename number
semantic authority ≠ schema format
semantic authority ≠ database
semantic authority ≠ model
```

## 4. Canonical identity rule

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

Future P0 architecture references MUST use an exact repository path/filename or a stable `ARCH-CLOSE-*` identifier. Bare references such as `document 18` are prohibited when the numeric prefix is not unique.

This avoids a large-scale rename that would create unnecessary historical-reference churn.

## 5. Closure-ID policy

P0 closure workstreams use stable identifiers:

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

## 6. Known numeric-prefix collisions

The System Architecture corpus contains historical organizational prefix collisions, including prefixes 17–22. These are not semantic conflicts because the exact path, title and authority determine identity.

Confirmed examples include:

| Prefix | Document A | Document B | Semantic conflict? | Governing rule |
|---|---|---|---|---|
| 17 | `17_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md` | `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` | No | exact filename / closure ID |
| 18 | `18_NVIDIA_PLATFORM_VALIDATION_MATRIX.md` | `18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md` | No | exact filename / closure ID |
| 19 | `19_EXECUTABLE_ARCHITECTURE_TEST_STRATEGY.md` | `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md` | No | exact filename / closure ID |
| 20 | `20_DEPLOYMENT_MANIFEST_SPECIFICATION.md` | `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md` | No | exact filename / closure ID |
| 21 | `21_ARCHITECTURE_COMPLETION_GATE.md` | `21_RUNTIME_RESOURCE_BUDGETS_AND_DETERMINISTIC_EXECUTION.md` | No | exact filename / closure ID |
| 22 | `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md` | `22_RUNTIME_VERSION_COMPATIBILITY_AND_LIFECYCLE.md` | No | exact filename / closure ID |

These are governed organizational collisions, not competing semantic authorities.

## 7. Historical lineage

Historical identifiers such as `06_107`, `07_108`, `08_110` and `09_111` remain in filenames because they preserve architecture lineage. They are not current sequential identifiers and must not be referenced by numeric prefix alone.

Archive content is retained for traceability and does not become current authority unless explicitly promoted by an approved decision.

## 8. Hardware numbering remediation — COMPLETE

The previous audit identified a Hardware-domain collision between:

- `24_GNSS_GPS_AND_GLOBAL_POSITIONING.md`
- former `24_HARDWARE_SELECTION_AND_BOM_BASELINE.md`

The BOM document has now been moved to:

`docs/05-hardware/26_HARDWARE_SELECTION_AND_BOM_BASELINE.md`

The current Hardware README records the remediation and canonical sequence:

```text
24_GNSS_GPS_AND_GLOBAL_POSITIONING.md
25_HARDWARE_VALIDATION_AND_TESTING.md
26_HARDWARE_SELECTION_AND_BOM_BASELINE.md
```

No current repository file may use the former `24_HARDWARE_SELECTION_AND_BOM_BASELINE.md` path as a current dependency.

**Action B: COMPLETE.**

## 9. Legacy audit refresh — COMPLETE

The current closure campaign and this 2026-08-19 audit supersede the older pre-closure file-number audit for current closure status.

Historical audits remain retained as evidence of architecture-corpus evolution. They must not be interpreted as current closure status.

**Action C: COMPLETE by explicit supersession/governance.**

## 10. Index synchronization — COMPLETE / final status synchronization pending

The Hardware README now records the resolved numbering state. The System Architecture README and master tracker remain the authoritative navigation/status surfaces and will receive their final System Architecture status synchronization after the 010 validation gate passes.

The current closure artifacts are discoverable through the System Architecture domain and stable `ARCH-CLOSE-*` identifiers.

**Action D: COMPLETE for document-index integrity; final status synchronization belongs to the final architecture gate.**

## 11. Automated integrity validator

The repository contains:

`scripts/validate_architecture_integrity.py`

and CI wiring:

`.github/workflows/architecture-integrity-validation.yml`

The validator checks:

1. explicit Markdown path references resolve to tracked repository files;
2. ambiguous numeric references are rejected unless locally unique;
3. closure IDs referenced by documents exist in the tracked architecture corpus;
4. duplicate numeric prefixes are reported as governed organizational labels.

The workflow executes this validator on pushes to `main` and `develop` and on pull requests.

The validator is therefore the canonical executable gate for Action E.

## 12. Final verification requirement

ARCH-CLOSE-010 cannot claim objective final closure until the validator has executed against the current post-remediation `main` revision and produced a passing result.

Required result:

```text
ARCHITECTURE INTEGRITY: PASS
errors = 0
unresolved document paths = 0
ambiguous numeric references = 0
unknown ARCH-CLOSE identifiers = 0
```

Duplicate numeric prefixes may remain because they are explicitly governed as non-authoritative organizational labels.

Migration warnings may remain only when they are locally resolvable and are not semantic ambiguity.

## 13. Required evidence artifact

The final 010 evidence record must include:

```text
validation_id
architecture_item = ARCH-CLOSE-010
software_revision / commit SHA
validator revision
repository revision
Markdown documents scanned
unresolved path count
ambiguous numeric reference count
unknown closure-ID count
duplicate-prefix count
migration-warning count
observed result
status
limitations
```

## 14. Current closure state

```text
A Exact-path policy              COMPLETE
B Hardware numbering            COMPLETE
C Legacy audit governance        COMPLETE
D Index/document integrity       COMPLETE
E Automated repository scan      PENDING EXECUTION
```

Therefore:

**ARCH-CLOSE-010 remains OPEN until Action E passes on the current repository revision.**

This is deliberate. The project will not claim a clean architecture-integrity gate based solely on prose or static inspection.

## 15. Architectural invariant

> **Every architecture dependency must resolve to an identifiable current authority, and no document number, filename, implementation artifact or historical reference may silently become a competing semantic authority. Final closure requires executable repository-wide verification.**
