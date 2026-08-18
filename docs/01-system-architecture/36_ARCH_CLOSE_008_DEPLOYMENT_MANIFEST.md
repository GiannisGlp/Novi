# 36 — ARCH-CLOSE-008 Deployment Manifest

**Status:** P0 architecture contract defined; implementation validation pending  
**Priority:** P0  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-008

## 1. Purpose

Define a machine-readable, immutable-by-revision deployment manifest that identifies everything required to reproduce a Novi runtime and everything needed to explain what produced an execution result.

The manifest is a provenance boundary, not a package manager. It records exact identities and compatibility constraints; installation tooling is responsible for resolving those identities.

## 2. Required manifest identity

Every deployment candidate MUST identify:

```text
manifest_id
manifest_schema_version
novi_revision
build_id
created_at
platform_profile
architecture
OS/runtime tuple
contract registry revision
schema versions
storage/migration version
model identifiers + hashes
model runtime versions
configuration revision/hash
sensor/hardware profile
security policy revision
feature flags
```

## 3. Proposed Stage-1 shape

```yaml
manifest_schema_version: "1.0.0"
manifest_id: "<immutable-id>"
novi_revision: "<git-sha>"
build_id: "<build-id>"
platform:
  profile: "mac-development"
  architecture: "arm64|x86_64"
runtime:
  os: "<exact-version>"
  language: "<exact-version>"
  compiler: "<exact-version>"
  ros2: null
contracts:
  registry_revision: "<git-sha-or-version>"
  schemas:
    - id: "<contract-id>"
      version: "<semver>"
storage:
  engine: "<candidate>"
  version: "<exact-version>"
  migration_revision: "<revision>"
models:
  - id: "<model-id>"
    version: "<version>"
    artifact_sha256: "<sha256>"
    runtime: "<runtime-version>"
configuration:
  revision: "<revision>"
  sha256: "<sha256>"
hardware:
  profile: "<hardware-profile>"
  sensors: []
security:
  policy_revision: "<revision>"
features: {}
validation:
  contract_gate: "<evidence-id>"
  compatibility_gate: "<evidence-id>"
```

The exact serialization format may evolve, but equivalent machine-readable fields are mandatory.

## 4. Immutability and provenance

A manifest is immutable once published. Changes create a new manifest revision.

A runtime MUST expose the manifest identity through diagnostics and include it in consequential event/model-invocation provenance.

A deployment without a resolvable manifest is **unreproducible** and cannot be treated as a validated release candidate.

## 5. Startup validation

Before authoritative state transitions begin, the runtime MUST validate:

1. Novi revision matches the manifest;
2. contract registry and schemas are compatible;
3. storage engine and migration revision are compatible;
4. configured models and artifact hashes match;
5. model runtimes satisfy declared constraints;
6. required configuration exists and matches its digest;
7. required hardware profile is present;
8. security policy is compatible;
9. required feature flags are understood.

A mismatch must produce an explicit `INCOMPATIBLE_DEPLOYMENT` result. The runtime must not silently continue into authoritative operation.

## 6. Development versus physical deployment

Stage 1 is Mac-first. The initial manifest therefore supports a `mac-development` profile with simulated, replayed or locally available sensors.

Future profiles may include:

```text
mac-development
simulation
agx-orin-64gb-mobile
thor-stationary
thor-mobile
```

The final compute profile remains undecided until workload characterization and physical validation are complete.

## 7. Model identity

Model names alone are insufficient. Every model used by a validated deployment must record:

- model ID;
- model version;
- artifact hash;
- quantization/precision;
- model runtime version;
- tokenizer/processor identity where applicable;
- required auxiliary assets;
- safety classification;
- fallback model where defined.

This prevents an apparently identical deployment from silently loading a different model artifact.

## 8. Configuration identity

Runtime configuration must be versioned and hashed. Sensitive secrets MUST NOT be embedded in the manifest.

The manifest records secret references/identifiers only, never secret values.

## 9. Hardware identity

A physical deployment manifest must identify the hardware profile and relevant component identities:

- compute module/platform;
- carrier board;
- storage device class/identity where required;
- sensor model/firmware;
- motor-controller model/firmware;
- safety MCU firmware;
- power-management/BMS firmware;
- thermal profile.

Serial numbers and other sensitive identifiers should be represented by controlled references or hashes where full disclosure is unnecessary.

## 10. Reproducibility requirements

A reviewer must be able to reconstruct a deployment from:

```text
manifest
+ source revision
+ dependency lockfiles
+ model artifacts/hashes
+ configuration revision
+ migrations
+ hardware profile
+ documented installation procedure
```

The manifest itself does not guarantee reproducibility if referenced artifacts are unavailable. Release validation must therefore verify artifact availability and integrity.

## 11. Deployment lifecycle

```text
DRAFT
  ↓
RESOLVED
  ↓
VALIDATED
  ↓
PUBLISHED
  ↓
INSTALLED
  ↓
RUNNING
  ↓
RETIRED
```

A manifest may not move to `PUBLISHED` without passing the applicable validation gates.

## 12. Rollback

Every published deployment must identify its immediate predecessor where one exists. Rollback must restore a previously validated manifest, not merely an older executable.

Storage migrations and model changes must declare whether rollback is supported, forward-only, or requires a recovery procedure.

## 13. Security requirements

The manifest must support integrity verification. Release artifacts should be signed where the deployment environment supports signing.

A manifest must never contain:

- API keys;
- passwords;
- private keys;
- personal secrets;
- unrestricted credentials.

## 14. Validation evidence

ARCH-CLOSE-008 requires executable evidence for:

- manifest schema validation;
- required-field validation;
- hash verification;
- startup compatibility rejection;
- reproducible environment reconstruction;
- model-artifact identity verification;
- configuration digest verification;
- rollback verification.

## 15. Closure criterion

ARCH-CLOSE-008 closes only when at least one Mac-first Novi deployment can be reconstructed and startup-validated from its manifest, with all referenced versions/artifacts pinned and the incompatible-deployment path tested.

This document therefore **defines the architecture contract but does not yet close the workstream**.

## 16. Architectural invariant

> **A Novi runtime is not a reproducible deployment unless its code, contracts, runtime, storage, models, configuration and hardware profile can be identified by an immutable deployment manifest.**
