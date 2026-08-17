# 10 — Architecture Validation & Traceability

**Status:** P0 normative validation framework  
**Purpose:** Ensure every important architectural statement is backed by a requirement, authoritative source, implementation contract and validation evidence.

## 1. Core rule

> A document is not considered implementation-ready merely because it is detailed. Every critical claim must be traceable and testable.

Required chain:

```text
REQUIREMENT
   ↓
ARCHITECTURAL DECISION
   ↓
CONTRACT
   ↓
IMPLEMENTATION
   ↓
TEST
   ↓
EVIDENCE
```

## 2. Evidence classes

### E0 — project assertion

Internal design intent. Not external validation.

### E1 — authoritative vendor/standards documentation

Examples:

- NVIDIA official documentation;
- official ROS documentation;
- official OS/runtime documentation;
- standards specifications;
- official hardware documentation.

### E2 — reproducible benchmark

A Novi-controlled test with versioned inputs, configuration and artifacts.

### E3 — integration validation

Cross-component test demonstrating compatibility.

### E4 — physical validation

Measured hardware result under controlled conditions.

### E5 — long-duration/reliability evidence

Repeated or extended testing demonstrating operational behavior.

A critical claim should not remain at E0 when higher evidence is required.

## 3. Source hierarchy

For technology facts:

```text
Official vendor/standards documentation
        ↓
Official project documentation
        ↓
Official source repository/release notes
        ↓
Reproducible benchmark
        ↓
Secondary technical source
        ↓
Community discussion
```

Secondary/community material can identify issues or alternatives but must not be the sole authority for a critical technology decision.

## 4. NVIDIA validation rule

For NVIDIA technology claims, prefer current NVIDIA sources:

- Jetson/JetPack documentation;
- NVIDIA Isaac Sim documentation;
- NVIDIA Isaac ROS documentation;
- NVIDIA TensorRT documentation;
- NVIDIA DeepStream documentation;
- NVIDIA Holoscan documentation;
- NVIDIA CUDA documentation;
- NVIDIA model/product documentation;
- NVIDIA release notes.

The installed NVIDIA skill catalog is used to route NVIDIA-specific research/workflows, while official NVIDIA documentation remains the source of truth for product claims. fileciteturn11file0L1-L20

## 5. Version rule

Every technology claim must identify, where applicable:

- product;
- version/release;
- target hardware;
- operating system;
- dependency versions;
- date verified;
- source.

Do not write "supported" without defining what version/platform was checked.

## 6. Compatibility matrix

Critical compatibility must be represented explicitly:

| Component | Version | OS | Hardware | Dependency | Evidence | Status |
|---|---|---|---|---|---|---|
| ROS 2 | Jazzy | Ubuntu 24.04 | x86/Jetson target | DDS/RMW | official docs + test | Candidate |
| Isaac Sim | current validated version | Ubuntu 24.04 | workstation GPU | ROS 2 Jazzy | NVIDIA docs | Candidate |
| JetPack | 7.2 | Ubuntu 24.04/L4T r39.2 | AGX Orin | BSP | NVIDIA docs | Candidate |
| DeepStream | 9.1 | Ubuntu 24.04/L4T r39.2 | Jetson Orin | JetPack 7.2 | NVIDIA docs | Candidate |
| TensorRT | JetPack-supported 10.x | JetPack target | Jetson | CUDA | NVIDIA docs | Candidate |

This table must be updated before ADR approval.

## 7. Requirement IDs

Every critical requirement receives an ID.

Examples:

```text
ARCH-001
ARCH-002
TIME-001
STATE-001
SAFETY-001
PRIV-001
RESOURCE-001
RUNTIME-001
VENDOR-001
```

## 8. Traceability record

Each requirement should map to:

```text
Requirement ID
 → rationale
 → source
 → architecture section
 → component/owner
 → contract
 → implementation task
 → test ID
 → evidence artifact
 → approval status
```

## 9. Architecture invariants

The following require explicit automated tests:

- adaptive model cannot bypass safety;
- model cannot obtain unrestricted filesystem/database/network authority;
- observations remain distinguishable from verified facts;
- event history is immutable;
- provenance survives projection;
- critical authorization is versioned;
- offline mode does not require network;
- stale approvals cannot authorize changed operations;
- deletion cannot be undone by stale replication/recovery;
- simulation results are labeled as simulated;
- physical measurements are distinguishable from predictions.

## 10. Technology validation

For each major technology:

```text
Requirement
 ↓
Candidate set
 ↓
Official documentation review
 ↓
License/security review
 ↓
Compatibility review
 ↓
Novi benchmark
 ↓
Failure-mode test
 ↓
Decision
```

## 11. Benchmark reproducibility

A benchmark must record:

- source commit;
- test code version;
- model version/digest;
- runtime version;
- OS;
- hardware;
- configuration;
- dataset/scenario version;
- seed;
- environmental conditions;
- measurement method;
- raw results;
- summary;
- known limitations.

## 12. No benchmark laundering

Do not substitute:

- vendor peak TOPS for Novi workload throughput;
- model-card quality for Novi task performance;
- simulator FPS for physical robot latency;
- synthetic data accuracy for real-world accuracy;
- a single successful run for reliability;
- theoretical power for measured power.

## 13. Architecture review gate

A P0 document is review-ready only when:

- scope is explicit;
- terminology is defined;
- dependencies are listed;
- assumptions are marked;
- technology claims are sourced;
- interfaces are defined;
- failure modes are documented;
- security/privacy impact is covered;
- resource requirements are covered;
- validation strategy exists;
- acceptance criteria exist.

## 14. Implementation gate

An architecture item is implementation-ready only when:

- the relevant P0 architecture is approved;
- applicable ADRs exist;
- contract schemas exist;
- test cases exist;
- dependencies are available;
- version compatibility is verified;
- rollback/recovery semantics exist for critical state;
- safety/security review is complete where applicable.

## 15. Change control

A change that affects a critical contract requires:

1. impact analysis;
2. affected documents;
3. compatibility assessment;
4. migration plan;
5. tests;
6. evidence;
7. ADR update where applicable.

## 16. Validation status vocabulary

```text
UNVERIFIED
DOCUMENTED
SOURCE-VERIFIED
BENCHMARKED
INTEGRATION-VERIFIED
PHYSICALLY-VERIFIED
LONG-DURATION-VERIFIED
SUPERSEDED
```

## 17. Final gate

Novi does not enter implementation merely because all documents exist.

It enters implementation when:

```text
DOCUMENTED
   +
SOURCE-VERIFIED
   +
CONTRACT-DEFINED
   +
TEST-DEFINED
   +
P0-APPROVED
   +
CRITICAL RISKS CONTROLLED
```

Only then is a subsystem considered ready.
