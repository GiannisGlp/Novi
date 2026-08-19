# 47 — ARCH-CLOSE-008 Deployment & Hardware Integration

**Status:** ARCHITECTURE DEFINED — target hardware validation pending  
**Priority:** P0  
**Authority:** System Architecture  
**Scope:** Mac-first development to eventual robot deployment.

## 1. Deployment principle

Novi is developed and functionally validated on the Mac first. Robot deployment is a portability and integration step, not a redesign of Novi's cognitive architecture.

```text
Mac development
   ↓
contract/integration validation
   ↓
model + workload characterization
   ↓
hardware selection
   ↓
robot runtime image
   ↓
sensor/actuator integration
   ↓
SIL → HIL → controlled physical validation
```

## 2. Deployment layers

### Layer A — Application

Novi cognitive/runtime services, contracts, configuration, orchestration, memory and safety policy.

### Layer B — AI runtime

Model artifacts, tokenizer/configuration, inference runtime, accelerator backend and model-specific optimization.

### Layer C — Platform runtime

OS, Python/native dependencies, drivers, CUDA/TensorRT/JetPack where applicable, device permissions and hardware SDKs.

### Layer D — Hardware

Compute module, carrier/interface, SSD, cameras, LiDAR, GNSS, IMU, thermal sensor/camera, night vision, microphones, speakers, motor controllers and actuators.

The boundaries must remain explicit so hardware-specific dependencies do not leak into the core cognitive contracts.

## 3. Mac baseline

The Mac remains the current development baseline. Development should use reproducible dependency definitions and record the exact Novi commit for executable evidence.

The Mac is not required to emulate the final robot's performance. It establishes correctness, contracts and functional behavior before hardware-specific optimization.

## 4. Robot runtime image

The eventual robot deployment should be reproducible from a versioned runtime specification containing:

```text
OS / architecture
GPU / accelerator
NVIDIA driver
CUDA
TensorRT
JetPack / platform release
Python + native runtime
sensor SDKs
inference runtime
storage runtime
model identifiers/hashes
Novi revision
contract/schema revisions
configuration revision
```

Hardware-specific versions remain deferred until AGX Orin 64 GB vs Thor and the model workload are selected.

## 5. Packaging

Deployment should produce an immutable, version-identifiable runtime image or equivalent reproducible environment. The image must not rely on undeclared packages installed manually on the robot.

Every deployment must expose:

- Novi version;
- runtime version tuple;
- model version/hash;
- contract/schema version;
- configuration version;
- hardware/platform identity.

## 6. Configuration

Separate immutable software from deployment configuration.

Configuration includes:

- sensor inventory and calibration references;
- network endpoints;
- hardware capabilities;
- model selection;
- safety limits;
- resource budgets;
- logging policy;
- storage/retention policy;
- time/synchronization configuration.

Secrets must never be committed into the runtime image or repository.

## 7. Hardware abstraction

Core Novi services must communicate with hardware through explicit interfaces/contracts.

Examples:

```text
Camera interface
Depth camera interface
Thermal camera interface
LiDAR interface
GNSS interface
IMU interface
Audio input/output interface
Actuator interface
Power/health interface
Time synchronization interface
```

This allows the sensor set and compute platform to evolve without changing cognitive logic.

## 8. Startup sequence

A robot startup must be gated rather than immediately enabling autonomous actuation:

```text
boot
 ↓
platform health
 ↓
storage health
 ↓
time synchronization
 ↓
sensor discovery
 ↓
calibration validation
 ↓
model/runtime load
 ↓
safety authorization
 ↓
contract/integration health
 ↓
Novi runtime ready
 ↓
actuation permitted
```

Any mandatory gate failure must prevent autonomous actuation and expose a diagnosable state.

## 9. Shutdown and recovery

The runtime must support:

- controlled shutdown;
- emergency-stop state;
- persistence flush where safe;
- restart recovery;
- incomplete-operation detection;
- model/runtime reload;
- sensor reconnection;
- configuration validation.

A robot restart must not silently restore an unsafe actuation state.

## 10. Offline operation

Core autonomous behavior must not require internet connectivity.

Internet access may be used for optional:

- updates;
- diagnostics;
- remote administration;
- model distribution;
- telemetry export.

Loss of connectivity must not disable local safety or core autonomous control unless a specific safety architecture requires it.

## 11. Updates and rollback

Updates must be atomic or otherwise recoverable. Each deployment must have a known-good rollback target.

Update order must preserve compatibility among:

```text
Novi code
contracts/schemas
models
runtime dependencies
hardware drivers
configuration
persistent state
```

Incompatible combinations must be rejected before autonomous operation.

## 12. Hardware profiles

### Profile M — Mac

Purpose: development, contract testing, functional AI evaluation and workload characterization.

### Profile R — Mobile robot

Purpose: 8–10 hour autonomous operation. Compute, sensors, actuation, battery and thermal system are jointly constrained.

### Profile S — Stationary robot

Purpose: continuous mains-powered operation. Higher sustained compute may be acceptable, but thermal, power supply and safety requirements remain.

AGX Orin 64 GB and Thor can be evaluated against these profiles independently; the architecture does not require one compute platform for every profile.

## 13. Validation stages

Deployment validation follows:

```text
D1 package reproducibility
 ↓
D2 Mac functional deployment
 ↓
D3 simulator / SIL
 ↓
D4 hardware-in-loop
 ↓
D5 sensor/actuator integration
 ↓
D6 controlled physical test
 ↓
D7 constrained/degraded operation
 ↓
D8 long-duration soak
```

No physical autonomy claim is inferred from a successful Mac deployment.

## 14. Acceptance criteria

ARCH-CLOSE-008 becomes validated when:

1. the Mac runtime is reproducible;
2. a versioned robot runtime specification exists;
3. hardware dependencies are isolated behind explicit interfaces;
4. startup/shutdown/recovery gates are executable;
5. deployment rollback is defined and tested;
6. offline operation is validated;
7. selected hardware profile has complete driver/runtime dependencies;
8. SIL/HIL/physical validation evidence exists at the appropriate stage.

## 15. Architectural invariant

> **Novi's cognitive architecture is hardware-independent; hardware-specific deployment is isolated behind versioned runtime, sensor, actuator and platform interfaces.**
