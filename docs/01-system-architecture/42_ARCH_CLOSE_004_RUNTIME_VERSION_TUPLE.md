# 42 — ARCH-CLOSE-004 Runtime / Version Tuple

**Status:** P0 architecture baseline  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-004 — Runtime/version tuple

## 1. Purpose

Define reproducible runtime boundaries without prematurely locking Novi to final robot hardware. The Mac is the current development baseline; Jetson/Thor deployment tuples remain conditional on the hardware decision and workload evidence.

## 2. Current Mac development tuple

| Component | Baseline | Status |
|---|---|---|
| OS | macOS on Apple Silicon | Supported development baseline |
| CPU architecture | arm64 | Required for current Mac baseline |
| Python | 3.14.6 observed in ARCH-CLOSE-003 benchmark | Observed evidence; pin after project dependency review |
| SQLite | 3.53.4 observed | Stage-1 candidate; final adoption pending ARCH-CLOSE-003 recovery gate |
| Novi revision | Record exact Git commit for executable evidence | Required |
| Model runtime | Not yet locked | Must be benchmarked against selected model |
| Inference backend | Not yet locked | Deferred until model/runtime evaluation |

The observed Python/SQLite versions above come from the committed ARCH-CLOSE-003 Mac benchmark. They are evidence, not yet a universal Novi compatibility promise.

## 3. Future robot tuple

The production robot tuple is intentionally **not fixed yet**.

It will be defined only after:

1. Novi runs functionally on the Mac;
2. model and sensor workloads are characterized;
3. AGX Orin 64 GB versus Thor evaluation is complete;
4. power/thermal constraints are measured;
5. required NVIDIA software versions are mapped to the selected hardware.

When hardware is selected, the tuple must include at minimum:

```text
OS / Linux distribution
CPU architecture
GPU / accelerator
NVIDIA driver
CUDA
TensorRT
JetPack / NVIDIA platform release
Python
C/C++ compiler/runtime
inference runtime
camera/LiDAR/GNSS SDK versions
SQLite / storage runtime
sensor middleware
model versions / hashes
Novi Git revision
contract/schema revisions
```

## 4. Compatibility policy

### Required now

- Mac development environment must be reproducible from documented dependencies.
- Exact Git revision must accompany benchmark/evidence runs.
- Runtime versions that affect correctness or numerical behaviour must be recorded.
- No architecture decision may depend on an unrecorded local package version.

### Deferred

- CUDA version
- JetPack release
- TensorRT version
- NVIDIA driver
- robot sensor SDK versions
- hardware-specific inference optimizations

These remain deferred until the hardware/model selection phase.

## 5. Version classes

Every dependency is classified as one of:

- **Pinned:** exact version required for reproducibility.
- **Range:** compatible semver/range permitted and tested.
- **Observed:** recorded from an experiment but not yet adopted as a requirement.
- **Deferred:** intentionally unspecified until a later architectural decision.
- **Forbidden:** known-incompatible version or configuration.

## 6. Evidence requirement

Executable evidence must record:

```text
Novi commit
runtime versions
OS
architecture
hardware
model identifier/version/hash
contract/schema versions
benchmark revision
configuration
```

This prevents a passing experiment from being detached from the environment that produced it.

## 7. Closure gate

ARCH-CLOSE-004 can close when:

- the Mac development tuple is reproducible;
- required dependency versions are classified;
- evidence captures exact revisions;
- unresolved hardware-specific versions are explicitly marked deferred;
- no current architecture dependency relies on an unspecified runtime.

Final robot-specific versions do **not** need to be selected to close the Mac-first architecture baseline.
