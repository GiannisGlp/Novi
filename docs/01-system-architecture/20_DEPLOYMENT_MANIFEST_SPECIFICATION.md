# 20 — Deployment Manifest Specification

**Status:** Normative architecture contract
**Priority:** P1

## 1. Purpose

A Novi deployment must be reproducible. The deployment manifest is the authoritative description of the software, hardware, model, configuration and policy versions that form a runnable Novi system.

It prevents the common failure mode where a system is described as "Jetson + ROS + NVIDIA stack" without recording the exact versions and artifacts that were tested.

## 2. Manifest Scope

A deployment manifest describes:

```text
hardware
firmware
OS / BSP
JetPack
CUDA
TensorRT
ROS 2
Isaac components
containers
models
model runtimes
Novi services
configuration
policies
safety profile
storage schema
network profile
observability configuration
```

## 3. Required Fields

Conceptual schema:

```yaml
manifest_version: "1"
deployment_id: "..."
profile: "mac|simulation|jetson|hil|physical"

hardware:
  platform: "jetson-agx-orin-64gb"
  revision: "..."
  memory_gb: 64
  storage: "..."

software:
  os: "..."
  jetpack: "..."
  l4t: "..."
  cuda: "..."
  tensorrt: "..."
  ros2: "jazzy"
  isaac_ros: "..."
  isaac_sim: "..."
  deepstream: "..."

containers:
  - name: "..."
    image: "..."
    digest: "sha256:..."

models:
  - name: "..."
    version: "..."
    artifact_digest: "..."
    runtime: "..."
    quantization: "..."

novi:
  git_commit: "..."
  schema_version: "..."
  configuration_version: "..."

policy:
  safety_policy_version: "..."
  authorization_policy_version: "..."

network:
  mode: "offline|local|connected"

observability:
  trace_schema_version: "..."
```

The final machine-readable schema belongs in implementation code and must be versioned.

## 4. Profiles

### Mac

Used for cognitive development and most software tests.

### Simulation

Isaac Sim + ROS 2 or equivalent simulation stack.

### Jetson

Edge software validation without unrestricted physical actuation.

### HIL

Jetson connected to controlled hardware interfaces with physical actuators isolated or constrained.

### Physical

Full robot deployment with hardware safety systems enabled.

## 5. Immutable Identification

Where practical, deployments must use:

- Git commit SHA;
- container image digest;
- model artifact digest;
- schema version;
- configuration version;
- policy version;
- hardware revision.

Human-readable version strings are useful but insufficient as the sole identity mechanism.

## 6. Startup Validation

Novi must validate the manifest before entering RUNNING state.

```text
LOAD MANIFEST
   ↓
SCHEMA VALIDATION
   ↓
HARDWARE CHECK
   ↓
SOFTWARE COMPATIBILITY CHECK
   ↓
MODEL CHECK
   ↓
POLICY CHECK
   ↓
SAFETY CONFIG CHECK
   ↓
READY
```

An incompatible tuple must enter a defined degraded or blocked state.

## 7. NVIDIA Compatibility

NVIDIA-specific versions must be validated against official NVIDIA support documentation before promotion.

For example, NVIDIA currently documents JetPack 7.2 / L4T r39.2 for the AGX Orin Developer Kit. citeturn1search0

NVIDIA currently recommends ROS 2 Jazzy/Humble for Isaac Sim 6.0 and documents Jazzy on Ubuntu 24.04. citeturn0search9

NVIDIA's TensorRT documentation currently requires Jetson deployments to use the TensorRT 10.x release supported by their JetPack version rather than TensorRT 11.2.1. citeturn0search3

These facts must be reflected in the validated manifest rather than copied as permanent assumptions.

## 8. Configuration Separation

The manifest identifies versions. Runtime configuration provides environment-specific values.

Do not encode secrets in the manifest.

Secrets must be supplied through the approved secret-management mechanism.

## 9. Policy Binding

The manifest must identify the safety and authorization policy versions used by the deployment.

A system must not claim to be running the same deployment if its safety policy has changed without a corresponding manifest/version change.

## 10. Model Binding

Model identity must include enough information to distinguish:

```text
model family
model version
weights
quantization
runtime
serving configuration
prompt/template version where behaviorally relevant
```

Changing any behaviorally relevant model artifact reopens model validation.

## 11. Deployment Promotion

A manifest can be promoted through:

```text
DEVELOPMENT
 ↓
SIMULATION
 ↓
JETSON
 ↓
HIL
 ↓
PHYSICAL
```

Each promotion records validation evidence against the exact manifest.

## 12. Rollback

A previous known-good manifest must remain identifiable.

Rollback must restore a complete compatible tuple rather than only changing one package.

## 13. Drift Detection

Runtime must compare actual environment against the manifest.

Drift examples:

- unexpected JetPack version;
- changed container digest;
- changed model artifact;
- modified safety policy;
- missing device;
- unsupported ROS package;
- configuration checksum mismatch.

Drift must be observable and, where safety-relevant, must block operation.

## 14. Acceptance Criteria

The deployment architecture is complete when a fresh machine can answer:

> Exactly which hardware, software, model, configuration and policy versions constitute this Novi instance?

and the answer can be reproduced from the manifest and repository state.
