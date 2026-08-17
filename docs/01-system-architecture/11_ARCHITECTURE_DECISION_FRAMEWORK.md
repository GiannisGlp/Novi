# 11 — Architecture Decision Framework

**Status:** P0 normative governance specification

## 1. Purpose

Architecture decisions become implementation constraints only when they are explicit, reviewable, evidence-backed and reversible or intentionally irreversible.

## 2. When an ADR is mandatory

Create an ADR for any decision affecting:

- core architecture;
- data/state semantics;
- safety;
- privacy;
- security;
- physical control;
- cross-domain contracts;
- technology selection;
- model selection;
- runtime/version baseline;
- storage semantics;
- deployment model;
- replication/consistency;
- recovery;
- hardware selection;
- vendor dependency;
- irreversible migration.

## 3. ADR lifecycle

```text
PROPOSED
 ↓
RESEARCHED
 ↓
BENCHMARKED
 ↓
REVIEWED
 ↓
ACCEPTED / REJECTED / DEFERRED
 ↓
IMPLEMENTED
 ↓
VALIDATED
```

## 4. Required ADR contents

Every critical ADR contains:

1. decision ID;
2. title;
3. status;
4. date;
5. problem;
6. requirements;
7. constraints;
8. candidates;
9. authoritative sources;
10. compatibility analysis;
11. benchmark results;
12. security analysis;
13. privacy analysis;
14. resource/power/thermal analysis where relevant;
15. alternatives considered;
16. decision;
17. consequences;
18. risks;
19. fallback;
20. migration/reversal plan;
21. validation evidence;
22. review/expiry date.

## 5. Technology decision rule

```text
Novi requirement
 ↓
Candidate technologies
 ↓
Official documentation
 ↓
License/security review
 ↓
Compatibility matrix
 ↓
Novi benchmark
 ↓
Failure-mode validation
 ↓
ADR
```

## 6. NVIDIA decisions

NVIDIA products must be evaluated using current NVIDIA documentation and version-specific compatibility information.

Examples of authoritative NVIDIA sources include:

- JetPack/Jetson documentation;
- Isaac ROS documentation;
- Isaac Sim documentation;
- TensorRT documentation;
- DeepStream documentation;
- CUDA documentation.

Current NVIDIA documentation confirms ROS 2 Jazzy as a tested/recommended Isaac Sim distribution and documents JetPack 7.2 for AGX Orin. citeturn0search4turn1search1

NVIDIA recommendation does not automatically equal Novi adoption.

## 7. Model decisions

A model ADR must include:

- exact model/version;
- license;
- provenance;
- context length;
- modality;
- parameter count;
- quantization;
- runtime;
- hardware requirements;
- latency;
- throughput;
- quality on Novi benchmarks;
- tool/structured-output behavior;
- failure modes;
- privacy/security implications;
- fallback model.

## 8. Hardware decisions

Hardware ADRs must include:

- functional requirement;
- physical constraints;
- electrical interface;
- power;
- thermal;
- mechanical envelope;
- driver/software compatibility;
- safety;
- calibration;
- synchronization;
- sourcing;
- replacement;
- validation result.

## 9. Version decisions

A version baseline is an architectural decision when incompatibility can affect implementation.

The ADR must freeze a tested tuple where relevant:

```text
OS
JetPack
CUDA
TensorRT
ROS 2
Isaac ROS
simulator
model runtime
model versions
container base
```

NVIDIA documentation demonstrates why individual package versions cannot be selected independently: DeepStream 9.1's Jetson package is based on JetPack 7.2/L4T r39.2 and its migration guide specifies TensorRT 10.x compatibility. citeturn0search1turn0search9

## 10. ADR review questions

Before acceptance ask:

- Does this satisfy the requirement?
- Is the source authoritative?
- Is the exact version known?
- Is it compatible with all target profiles?
- Has it been benchmarked?
- What happens when it fails?
- Can it operate offline?
- What is the security impact?
- What is the privacy impact?
- What is the resource/power/thermal impact?
- What is the replacement/fallback?
- Does it leak vendor details into semantic contracts?
- Can we test it?
- Can we recover from it?

## 11. Decision confidence

Use:

```text
LOW
MEDIUM
HIGH
VALIDATED
```

`VALIDATED` requires reproducible evidence, not confidence in documentation alone.

## 12. Expiry and revalidation

Fast-moving technology decisions should carry a review trigger or date.

Revalidate when:

- major version changes;
- hardware target changes;
- OS changes;
- security advisory;
- license change;
- upstream support changes;
- benchmark failure;
- new workload requirements.

## 13. Decision registry

The architecture directory should maintain an ADR index containing:

```text
ADR ID
TITLE
STATUS
DATE
OWNER
RELATED DOCS
RELATED TECHNOLOGIES
VALIDATION STATUS
REVIEW DATE
```

## 14. No silent adoption

A technology mentioned in a research document, README, architecture diagram or benchmark is **not adopted** until its ADR says so.

## 15. Current priority ADRs

The first architecture ADR set should cover:

1. ROS 2 / Ubuntu baseline.
2. Robotics control boundary (`ros2_control`).
3. Navigation/localization boundary.
4. Simulation baseline and Isaac Sim integration.
5. Durable-state storage technology.
6. Knowledge storage technology.
7. Vector retrieval technology.
8. Model runtime architecture.
9. Initial model set.
10. Speech/ASR/TTS architecture.
11. Perception backend boundaries.
12. Observability stack.
13. Deployment/reproducibility.
14. Security/secrets.
15. Hardware compute baseline.

## 16. Final rule

> **A technology is a candidate until evidence and an approved ADR make it an adopted implementation.**
