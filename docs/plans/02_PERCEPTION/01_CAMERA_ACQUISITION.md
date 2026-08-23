# Perception — Camera Acquisition Pipeline

## Objective

Replace `DemoCamera` as the only real camera path: a live camera acquisition pipeline on the Mac body that delivers frames into world state through the existing capability interfaces, giving the brain real visual input for M1 ("Real Neural Perception") and every downstream recognition capability.

This doc owns **acquisition only** — frames, timing, calibration identity, world-state delivery. Recognition (faces/objects) is specified separately in [`02_FACE_AND_OBJECT_RECOGNITION.md`](02_FACE_AND_OBJECT_RECOGNITION.md).

## Scope

In scope:

- single-camera live acquisition on macOS (Mac body = temporary body);
- frame lifecycle: capture → timestamp → deliver;
- calibration/sensor identity fields (hardware docs §21 pattern, minimal form);
- world-state integration contract;
- deterministic fake camera for CI (extends the `DemoCamera` convention).

Out of scope (deferred to robot hardware phase): multi-camera arrays, MIPI/GMSL transport, hardware synchronization/PTP, LiDAR/depth fusion. Single-stream now proves the brain-facing contract; the multi-sensor version later scales the same contract.

## Provider contract

```text
CameraProvider (protocol)
  open(config) -> None
  read() -> CameraFrame        # non-blocking or bounded-wait
  close() -> None
  health() -> CameraHealth     # AVAILABLE / DEGRADED / FAILED / UNKNOWN
```

`CameraFrame` already exists in the brain; this pipeline guarantees it arrives with:

| Field | Requirement |
|---|---|
| image data | RGB, resolution/fps configurable (baseline 640×480 @ 15–30 fps) |
| sensor timestamp | capture-time monotonic + wall clock |
| frame id | monotonic sequence for gap detection |
| calibration identity | camera id, model placeholder, calibration version (minimal now, full per §21 on robot) |
| provenance | provider backend, config hash |

## Acquisition design

```text
AVFoundation/OpenCV capture thread
        │  (bounded queue, drop-oldest under load)
        ▼
frame bus ──► AgentInput(vision) ──► BrainDriver.drive()   [cognitive-rate sampling]
        └────► perception consumers (detectors)            [full-rate]
```

Requirements:

1. Capture runs on its own OS thread; the cognitive loop samples at its own rate and never blocks on camera I/O.
2. Bounded queue with explicit drop policy; dropped-frame counters are telemetry, not silent loss.
3. Health state changes (camera unplugged, permissions denied) surface into the hardware-health view (`AVAILABLE → DEGRADED → FAILED`) and degrade behavior explicitly — no silent black frames.
4. macOS camera permission is an explicit setup gate with a deterministic test double so CI never touches hardware.

## World-state integration

Frames are evidence into the world model:

- visible-object updates carry frame id + timestamp provenance;
- "currently visible" decays if frames stop arriving (stale-vision handling);
- spatial context tags (`place`, `seen_at`, frame reference) attach to admitted perceptions — feeding exit-contract B3 requirement 3 (spatial/temporal binding, gap G7).

## Deterministic testing

CI uses scripted frame sequences (the `DemoCamera` lineage): moving synthetic objects, occlusion, dropout mid-sequence. Validates: queue/drop behavior, health transitions, stale-vision decay, world-state provenance chains. No hardware in CI.

## Evidence gates

- 30-minute live run: continuous frames, zero unhandled failures, health telemetry recorded.
- Dropout injection: unplug/recover camera → DEGRADED → recovery event logged, cognition informed.
- First real SSDLite-class detection evidence over live frames (feeds `04_SPECIALIST_PERCEPTION.md` candidate validation).

## Resource parity

OpenCV/AVFoundation capture maps to V4L2/Argus on Jetson behind the same `CameraProvider` protocol. Resolution/FPS baseline deliberately modest — Jetson-plausible from day one.

## Status

**PLANNED / DOC PHASE.** Sequencing: protocol + fake hardening → AVFoundation/OpenCV provider → health/degradation paths → world-state provenance → live evidence run.
