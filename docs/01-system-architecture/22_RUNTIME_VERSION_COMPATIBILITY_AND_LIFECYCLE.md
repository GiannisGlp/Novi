# 22 — Runtime Version Compatibility & Lifecycle

**Status:** P0 normative architecture specification  
**Owner:** System Architecture  
**Scope:** ROS 2, NVIDIA Isaac Sim/Isaac ROS, CUDA, TensorRT, drivers, models, containers, firmware, hardware and Novi runtime components

## 1. Purpose

Novi must never depend on an undocumented combination of versions that happens to work on one machine.

This document defines the compatibility and lifecycle rules for the software/hardware stack.

It does **not** select final versions. Version selection is an engineering decision recorded through the repository's technology/ADR process and validated against this matrix.

> A version is adoptable only when its complete dependency set is known, tested and reproducible.

## 2. Compatibility chain

```text
Hardware
   ↓
Firmware / BIOS / device configuration
   ↓
OS + kernel
   ↓
GPU driver
   ↓
CUDA
   ↓
TensorRT / acceleration libraries
   ↓
ROS 2
   ↓
Isaac ROS / robotics packages
   ↓
Novi runtime
   ↓
Models
   ↓
Application configuration
```

Simulation adds:

```text
Isaac Sim
   ↓
ROS 2 bridge / interfaces
   ↓
Novi simulation runtime
```

A failure anywhere in this chain can invalidate higher-level validation.

## 3. Version manifest

Every reproducible Novi deployment MUST have a machine-readable manifest containing at minimum:

```text
platform
hardware_model
hardware_revision
firmware_version
os_distribution
os_version
kernel_version
gpu_driver_version
cuda_version
tensorrt_version
ros_distribution
ros_patch_version
isaac_ros_release
isaac_sim_version
novi_runtime_version
model_artifact_ids
model_runtime_versions
container_image_digests
configuration_revision
contract_versions
```

Human-readable documentation may summarize the manifest but cannot replace it.

## 4. Compatibility matrix

The project MUST maintain a matrix with:

| Component | Version | Supported with | Validation status | Evidence | Lifecycle |
|---|---|---|---|---|---|
| Hardware | TBD | platform stack | unvalidated | benchmark | active/candidate |
| OS | TBD | kernel/driver | unvalidated | test | candidate |
| GPU driver | TBD | CUDA | unvalidated | test | candidate |
| CUDA | TBD | driver/TensorRT | unvalidated | test | candidate |
| TensorRT | TBD | CUDA/runtime | unvalidated | test | candidate |
| ROS 2 | TBD | Isaac ROS/Novi | unvalidated | integration | candidate |
| Isaac ROS | TBD | ROS 2/Jetson or NVIDIA platform | unvalidated | integration | candidate |
| Isaac Sim | TBD | ROS 2/Isaac ROS workflow | unvalidated | simulation | candidate |
| Novi runtime | TBD | full stack | unvalidated | system test | development |
| Model | TBD | runtime/hardware | unvalidated | benchmark | candidate |

`TBD` is intentional until validation establishes the actual stack.

## 5. NVIDIA compatibility is release-specific

NVIDIA documentation demonstrates that Isaac ROS and Isaac Sim compatibility depends on specific releases rather than being universally interchangeable. NVIDIA's Isaac ROS documentation provides release compatibility tables, and current Isaac Sim documentation recommends ROS 2 Humble and Jazzy, with version-specific integration details. citeturn0search0turn0search3

Therefore Novi MUST record exact versions rather than statements such as:

```text
"latest Isaac ROS"
"latest CUDA"
"ROS 2"
"TensorRT latest"
```

Those are not reproducible dependencies.

## 6. ROS 2 distribution policy

ROS 2 distribution selection is a system-level decision.

As of the current NVIDIA Isaac Sim documentation, Humble and Jazzy are the officially tested/recommended ROS 2 distributions for Isaac Sim, while other native distributions may be experimentally supported depending on platform/version. citeturn0search3

Novi should select one production ROS 2 baseline and one explicitly documented simulation/development baseline where necessary.

Mixing distributions inside one deployment is prohibited unless an explicit compatibility test and interface boundary justify it.

## 7. Isaac Sim compatibility

Isaac Sim is a validation/simulation dependency, not automatically a production robot dependency.

The repository MUST record:

- Isaac Sim version;
- ROS 2 distribution;
- ROS bridge version/extension;
- relevant Isaac ROS release;
- Python version where applicable;
- operating system;
- GPU/driver requirements;
- simulation asset revision;
- scenario/test-suite revision.

NVIDIA's current Isaac Sim ROS documentation also identifies environment and distribution constraints, including Python-version considerations for specific releases. citeturn0search1

## 8. ROS 2 environment consistency

A simulation or robot test is invalid if the ROS environment is ambiguous.

The validation environment MUST record and, where applicable, verify:

- `ROS_DISTRO`;
- sourced ROS installation;
- DDS middleware/configuration;
- `ROS_DOMAIN_ID`;
- ROS 2 workspace revision;
- message/interface versions.

NVIDIA documents that mismatched ROS environments, DDS middleware, or `ROS_DOMAIN_ID` can prevent Isaac Sim topics from appearing correctly across processes. citeturn0search2

## 9. Containers

Containers should be used where they improve reproducibility, isolation or deployment portability.

Every production container MUST be referenced by immutable image digest, not only a mutable tag.

Example:

```text
novi-brain:<tag>
```

is insufficient for reproducibility.

```text
novi-brain@sha256:<digest>
```

is the deployment identity.

Container images MUST declare their:

- base image;
- architecture;
- CUDA/runtime expectations;
- ROS distribution;
- Novi version;
- model dependencies;
- contract versions.

## 10. Model compatibility

A model is not compatible merely because it loads.

Compatibility requires validation of:

- model artifact identity;
- architecture;
- input/output schema;
- preprocessing/postprocessing;
- tokenizer/processor where applicable;
- precision;
- TensorRT/ONNX/runtime compatibility where used;
- GPU architecture;
- memory requirements;
- latency budget;
- numerical behavior;
- safety constraints;
- expected quality metrics.

A model runtime conversion is a new validated artifact.

## 11. Driver and accelerator lifecycle

GPU driver, CUDA and TensorRT changes MUST be treated as potentially system-wide changes.

A driver upgrade can affect:

- CUDA compatibility;
- TensorRT behavior;
- inference performance;
- memory usage;
- Isaac ROS acceleration;
- simulation;
- sensor pipelines.

Therefore no such upgrade is considered routine maintenance without regression validation.

## 12. Hardware-specific compatibility

The same software version can behave differently across hardware generations.

The compatibility matrix MUST distinguish at least:

```text
platform family
hardware model
hardware revision
GPU architecture
memory capacity
sensor configuration
actuator configuration
```

This is especially important for the decision of whether Novi eventually moves to Jetson.

Jetson adoption remains a **validated deployment decision**, not an architectural assumption.

## 13. Development / simulation / HIL / physical environments

Novi MUST distinguish four validation environments:

```text
DEV
 ↓
SIMULATION
 ↓
HIL / controlled integration
 ↓
PHYSICAL ROBOT
```

A test passing in an earlier environment does not automatically certify the next environment.

Each environment needs its own manifest and validation evidence.

## 14. Promotion gates

A stack promotion should follow:

```text
candidate
  ↓
static compatibility check
  ↓
unit/integration validation
  ↓
simulation validation
  ↓
performance/resource validation
  ↓
HIL validation where applicable
  ↓
physical validation where applicable
  ↓
safety regression
  ↓
adopt
```

Failure at a gate blocks promotion unless an explicitly documented exception is approved.

## 15. Upgrade policy

Every upgrade MUST identify:

- current version;
- target version;
- reason;
- affected components;
- compatibility evidence;
- performance impact;
- safety impact;
- migration steps;
- rollback procedure;
- validation results.

Do not combine unrelated foundational upgrades into one change when doing so prevents fault isolation.

## 16. Rollback

Every production stack upgrade MUST have a known rollback path.

Rollback must restore:

- software versions;
- model artifacts;
- configuration;
- contract compatibility;
- container images;
- relevant firmware where safely reversible.

The rollback procedure itself must be tested before a high-risk upgrade is considered complete.

## 17. Deprecation

A component approaching end-of-life MUST be recorded with:

```text
current status
last validated version
end-of-support date if known
replacement candidate
migration owner
migration test plan
```

Novi must not silently move to a replacement merely because the old dependency became inconvenient.

## 18. Security and supply-chain integrity

Version identity is also a security property.

Production dependencies MUST be traceable to:

- source/repository;
- release/version;
- artifact digest where available;
- build provenance where available;
- vulnerability review;
- license review.

Unsigned or unverifiable artifacts must not become production dependencies without an explicit security decision.

## 19. Reproducibility

A clean machine should be able to reconstruct a validated environment from version-controlled manifests and approved artifacts.

The definition of reproducibility is:

```text
same manifest
+
same artifact identities
+
same configuration
+
same hardware class
→
materially equivalent runtime
```

"It worked on my machine" is not validation evidence.

## 20. Observability

Runtime must expose enough information to diagnose compatibility failures:

- software versions;
- loaded model IDs;
- contract versions;
- hardware identity;
- driver/runtime versions;
- container digest;
- startup compatibility checks;
- failed dependency checks.

Startup should fail clearly when a mandatory incompatible dependency is detected.

## 21. Compatibility checker

Before production startup, Novi should run a deterministic compatibility check:

```text
load manifest
     ↓
identify hardware
     ↓
identify installed runtime
     ↓
resolve required dependencies
     ↓
check contract compatibility
     ↓
check model compatibility
     ↓
check resource requirements
     ↓
check safety baseline
     ↓
PASS / DEGRADED / BLOCKED
```

A blocked system must not silently continue in an unvalidated configuration.

## 22. NVIDIA-specific validation boundary

NVIDIA components should be validated using NVIDIA's release-specific compatibility information and the actual Novi workload.

Current NVIDIA documentation shows that Isaac Sim provides ROS 2 integration through its bridge and that Isaac ROS is an NVIDIA-accelerated ROS 2 package family; the exact release pair remains part of compatibility validation. citeturn0search4turn0search10

Novi must therefore avoid hard-coding assumptions such as:

```text
Isaac Sim → any ROS 2
Isaac ROS → any CUDA
TensorRT → any GPU
```

Instead, the manifest records the tested combination.

## 23. No Jetson lock-in

The architecture remains platform-neutral.

Novi's semantic brain contracts, autonomy, cognition and memory must not depend directly on Jetson-specific APIs.

Platform-specific acceleration belongs behind adapters/runtime boundaries.

This permits:

```text
Development workstation
        ↓
Simulation
        ↓
Alternative edge compute
        ↓
Jetson when justified
```

without redesigning Novi's cognitive architecture.

## 24. Required artifacts before physical deployment

Before committing to a production compute platform, Novi MUST have:

- compatibility matrix;
- complete runtime manifest;
- benchmark results;
- resource measurements;
- thermal measurements;
- startup compatibility checks;
- rollback procedure;
- model compatibility evidence;
- safety regression results;
- simulation/HIL evidence;
- physical acceptance evidence.

## 25. Definition of done

This architecture is complete when:

- every deployed component has an exact version identity;
- compatibility relationships are explicit;
- manifests are machine-readable;
- container digests are pinned;
- model artifacts are versioned;
- ROS 2/Isaac compatibility is tested;
- driver/CUDA/TensorRT relationships are tested;
- hardware-specific differences are captured;
- promotion gates are defined;
- rollback is tested;
- startup compatibility checks exist;
- dependency upgrades are auditable;
- no production dependency relies on an unrecorded "latest" version;
- Jetson remains an evidence-based deployment choice.

## 26. Architectural invariant

> **Novi is deployed as a validated stack, not as a collection of individually working packages.**

Every version, model, driver, container, interface and hardware combination must be treated as part of the system configuration and validated accordingly.
