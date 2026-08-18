# 34 — Sensor Requirements Addendum: Gyroscope and Night Vision

**Status:** Requirements baseline  
**Priority:** P0  
**Authority:** System Architecture / Hardware integration boundary  
**Parent document:** `33_NOVI_SENSOR_AND_PERCEPTION_ARCHITECTURE.md`

## 1. Decision

Two requirements are explicitly elevated into the Novi sensing baseline:

1. **Gyroscope — mandatory P0 capability.**
2. **Dedicated night-vision camera — mandatory P0 capability for the target full-sensing architecture.**

The gyroscope is normally part of the IMU rather than a separate physical device. The requirement therefore means that the selected IMU must provide a suitable 3-axis gyroscope; it does not imply purchasing a standalone gyroscope.

Night vision is a distinct modality from RGB, RGB-D, thermal and LiDAR and must not be assumed to be satisfied by any of them.

## 2. Gyroscope requirement

Novi requires a 3-axis angular-rate sensor as part of its inertial measurement subsystem.

The selected IMU should expose:

- angular velocity around X/Y/Z;
- calibrated timestamps;
- covariance/quality information;
- calibration status;
- temperature information where available;
- bias/noise characteristics;
- suitable dynamic range for the expected robot motion;
- sufficiently high output rate for the control/localization workload;
- preferably hardware timestamping and deterministic synchronization.

### Primary uses

- attitude estimation;
- visual-inertial odometry;
- stabilization;
- motion compensation;
- LiDAR/camera motion compensation;
- detection of unexpected rotation;
- wheel-slip and motion consistency checks;
- robot-state estimation;
- temporal alignment of high-rate motion with slower perception.

### Architectural rule

Gyroscope data must not be treated as unquestionable truth. Bias, drift, vibration and temperature effects must be represented in the state estimator and uncertainty model.

The preferred architecture is:

```text
Gyroscope + Accelerometer
          ↓
       IMU driver
          ↓
 timestamp + calibration + covariance
          ↓
 state estimator / VIO / SLAM
          ↓
 pose + velocity + uncertainty
```

A magnetometer may provide an additional heading observation, but should not be relied upon in magnetically disturbed environments.

## 3. Night-vision requirement

Novi should have at least one dedicated camera capable of useful perception in very low-light/night conditions.

This is deliberately separate from thermal imaging.

### Candidate technologies

#### A. NIR / IR-sensitive camera

A camera with strong near-infrared sensitivity can operate with active IR illumination when required.

Advantages:

- image structure remains closer to ordinary camera perception;
- useful for object/scene recognition;
- can operate in darkness with controlled illumination;
- potentially lower cost than specialized thermal systems.

Trade-offs:

- active illumination consumes power;
- reflective surfaces can saturate;
- illumination range is finite;
- privacy considerations must be documented.

#### B. Starlight / ultra-low-light camera

A highly sensitive visible-light camera can preserve passive operation in very low illumination.

Advantages:

- no active illumination required;
- potentially natural-looking images;
- lower additional power than an IR illuminator.

Trade-offs:

- performance depends on available photons;
- motion blur can increase with long exposure;
- very dark scenes can still become unusable.

## 4. Night vision vs other sensors

These modalities have different physical information:

```text
RGB
  visible-spectrum appearance

RGB-D
  visible appearance + geometric depth

Night vision
  low-light / NIR visual structure

Thermal
  emitted infrared / temperature-related radiance

LiDAR
  active geometric range
```

Therefore a thermal camera does **not** replace a night-vision camera, and a night-vision camera does **not** replace LiDAR or depth sensing.

## 5. Night-vision integration

The perception pipeline should normalize night-vision output into the same high-level perception interfaces used by other cameras while preserving modality metadata.

Example observation metadata:

```text
modality = night_vision
illumination = passive | active_ir
exposure_us = ...
illuminator_state = on | off
camera_id = ...
timestamp = ...
calibration_id = ...
confidence = ...
```

This prevents the cognition layer from confusing an IR image with an ordinary RGB observation.

## 6. Synchronization

The night-vision camera should be synchronized with the other perception sensors where practical.

At minimum record:

- capture timestamp;
- receipt timestamp;
- clock domain;
- exposure duration;
- camera calibration revision;
- illumination state.

The gyroscope must participate in the same temporal architecture so motion compensation can correctly associate angular motion with camera exposure.

## 7. Sensor-fusion role

A representative night-time perception stack is:

```text
RGB camera ───────┐
RGB-D camera ─────┤
Night camera ──────┤
Thermal camera ────┤
3D LiDAR ──────────┤
IMU gyro/accel ────┤
Wheel encoders ────┤
GNSS ──────────────┘
         ↓
   sensor fusion
         ↓
  world observation
         ↓
 localization / perception
         ↓
 cognition / autonomy
```

No individual modality is permitted to silently become the universal source of truth.

## 8. Selection gate

The final gyroscope/IMU and night-vision camera are selected only after the Mac-first workload establishes the required:

- sampling rate;
- latency;
- synchronization precision;
- field of view;
- dynamic range;
- low-light threshold;
- motion-blur tolerance;
- power;
- bandwidth;
- compute load;
- physical size/weight;
- environmental rating;
- driver/ROS 2 support;
- calibration process;
- cost.

## 9. Status

```text
Gyroscope capability       P0 / REQUIRED / component open
Night-vision camera        P0 / REQUIRED / component open
Thermal camera             P0 / REQUIRED / component open
RGB cameras                P0 / REQUIRED / component open
RGB-D cameras              P0 / REQUIRED / component open
3D LiDAR                   P0 / REQUIRED / component open
GNSS                       P0 / REQUIRED / component open
Microphone array           P0 / REQUIRED / component open
```

This addendum does **not** select vendors or final components. It closes the requirements ambiguity while preserving the later evidence-based hardware-selection gate.
