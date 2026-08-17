# Novi Spatial and Proprioceptive Fusion

**Status:** Critical architecture specification  
**Priority:** P0  
**Scope:** Embodied state estimation between multimodal perception and the Novi world model  
**Canonical implementation boundary:** `SpatialStateEstimator` / `EmbodiedState` contract to be finalized by ADRs

## 1. Purpose

Novi must know not only what exists around him, but where he is, how his body is configured, how his body is moving, how confident those estimates are, and how observations relate to his body and the environment.

This document defines the spatial and proprioceptive fusion layer that converts heterogeneous observations into a time-indexed, frame-consistent estimate of Novi's embodied state.

This layer is foundational for:

- safe movement;
- navigation;
- visual attention and orientation;
- manipulation;
- multimodal association;
- world-model updates;
- action-result attribution;
- learned policy inputs;
- simulation-to-real validation;
- recovery after localization or sensor degradation.

It is **not** the safety controller, motor controller, or complete world model. It provides state estimates and uncertainty to those systems.

## 2. Core principle

Novi must maintain a distinction between:

```text
measurement
  !=
raw sensor observation
  !=
state estimate
  !=
world-model belief
  !=
truth
```

Every estimated pose, velocity, orientation, transform, contact state, or body configuration must have provenance, timestamp, frame semantics, uncertainty/quality information, and an identifiable estimation method.

## 3. Embodied state model

The minimum embodied state is:

```text
EmbodiedState
├── timestamp
├── clock_domain
├── frame_graph_version
├── base_pose
│   ├── position
│   └── orientation
├── linear_velocity
├── angular_velocity
├── linear_acceleration
├── gravity_direction
├── joint_positions
├── joint_velocities
├── joint_efforts / currents when available
├── wheel_states when applicable
├── contact_states when available
├── sensor_poses
├── localization_status
├── motion_status
├── covariance / uncertainty
├── source_provenance
└── quality / freshness
```

Additional robot-specific state may include battery state, thermal state, actuator health, payload state and end-effector state. Those are referenced by this layer but remain owned by their respective subsystem contracts.

## 4. Coordinate-frame contract

The frame graph must be explicit and machine-verifiable.

The baseline ROS 2 convention is expected to use a structure equivalent to:

```text
map
 └── odom
      └── base_link
           ├── sensor frames
           ├── wheel frames
           ├── imu_link
           └── body / actuator frames
```

The exact robot frame tree must be defined in the robot-description and TF architecture. No implementation may rely on an undocumented implicit frame relationship.

Required properties:

- every frame has a unique identifier;
- parent-child relationships are explicit;
- static and dynamic transforms are distinguished;
- transform timestamps are meaningful;
- frame authority is defined;
- competing publishers are prohibited unless explicitly coordinated;
- stale transforms are detectable;
- calibration versions can be associated with sensor transforms;
- frame-tree validity can be tested automatically.

NVIDIA Isaac Sim currently documents publishing full articulation transform trees and odometry through ROS 2, including `/tf`, `/tf_static`, and odometry. citeturn0search0

## 5. Sensor inputs

Candidate inputs include:

### 5.1 IMU

- angular velocity;
- linear acceleration;
- gravity direction where available;
- timestamp;
- sensor frame;
- covariance/quality.

IMU measurements are particularly important for high-rate motion estimation and short-term propagation.

NVIDIA's current Isaac Sim documentation exposes IMU angular velocity, linear acceleration and orientation and demonstrates publishing IMU data through ROS 2. citeturn0search3turn0search6

### 5.2 Wheel / joint encoders

Where Novi uses wheeled or articulated locomotion, encoders provide:

- wheel/joint position;
- velocity;
- direction;
- motion constraints;
- odometric increments.

Encoder data must not be treated as globally correct position. Slip, backlash, quantization and mechanical errors must be modeled or detected.

### 5.3 Visual odometry / VSLAM

Vision can provide motion constraints and global/local pose estimates. These estimates must carry tracking status and uncertainty and must be checked for loss of tracking, relocalization and map changes.

### 5.4 LiDAR / geometric localization

LiDAR can provide geometric constraints for localization and mapping. It is complementary to visual estimates and should not automatically be assumed authoritative in all environments.

### 5.5 External references

Potential inputs include:

- fiducials;
- GNSS where applicable;
- UWB;
- motion-capture systems;
- surveyed landmarks;
- simulation ground truth.

External references must be explicitly classified as operational sensing, calibration/reference data, or evaluation-only ground truth.

## 6. Estimation architecture

Novi should use a layered estimator rather than one monolithic neural network:

```text
high-rate inertial / encoder propagation
                 ↓
        local motion estimate
                 ↓
 visual / lidar / landmark corrections
                 ↓
       state consistency checks
                 ↓
     localization / pose estimate
                 ↓
          embodied state
                 ↓
       world-model consumers
```

A neural estimator may eventually be evaluated for particular workloads, but the canonical state-estimation contract must remain independent of any particular learned model.

## 7. Time alignment

Fusion is only meaningful when measurements are temporally comparable.

Every measurement must carry:

- acquisition timestamp;
- publication/arrival timestamp where useful;
- clock domain;
- estimated synchronization quality;
- sequence identifier where available.

The estimator must explicitly handle:

- delayed measurements;
- out-of-order measurements;
- dropped samples;
- duplicate samples;
- clock jumps;
- simulation time;
- replay time;
- sensor-specific rates.

NVIDIA's current Isaac Sim documentation demonstrates independent publish rates for IMU, RTX LiDAR and camera sensors, making explicit rate/timing handling necessary even in simulation. citeturn0search4

## 8. Calibration

Calibration is part of the system state, not an undocumented installation step.

Required calibration classes include:

- IMU bias/noise parameters;
- camera intrinsics;
- camera-to-body extrinsics;
- LiDAR-to-body extrinsics;
- camera-to-LiDAR transforms;
- encoder scale factors;
- wheel radius and separation where relevant;
- joint zero offsets;
- sensor orientation;
- time offsets where measurable.

Each calibration artifact must have:

- unique identity;
- version;
- creation time;
- method;
- equipment/environment information;
- validity range where applicable;
- verification result;
- owner;
- cryptographic identity where persisted.

## 9. Uncertainty

Uncertainty is a first-class output.

The estimator must expose enough information for downstream consumers to distinguish:

```text
high-confidence state
usable state with uncertainty
stale state
degraded state
invalid state
```

Where covariance is mathematically appropriate it should be represented explicitly. For other state classes, calibrated confidence/quality measures may be used.

Downstream systems must never silently substitute an old state for a fresh state without knowing its age.

## 10. Localization states

The canonical localization state machine should include at least:

```text
UNINITIALIZED
    ↓
INITIALIZING
    ↓
TRACKING
    ├── DEGRADED
    ├── LOST
    └── RELOCALIZING
              ↓
           TRACKING
```

Transitions must be driven by measurable estimator health rather than arbitrary timers.

When localization is lost, Novi must:

1. report loss explicitly;
2. prevent consumers from assuming global pose is valid;
3. retain safe local state if available;
4. attempt recovery through permitted mechanisms;
5. escalate or stop according to the safety policy when required.

## 11. Motion state

Novi should maintain a motion-state abstraction independent of any particular controller:

```text
STATIONARY
STARTING
MOVING
TURNING
REVERSING
STOPPING
CONTACT / CONSTRAINED
RECOVERING
FAULTED
```

These states are descriptive estimates, not actuator commands.

Motion state should incorporate velocity, acceleration, commanded motion, observed motion, contact information and estimator confidence.

## 12. Proprioception

Proprioception is Novi's internal sense of its own body.

It must cover, as applicable:

- joint position;
- joint velocity;
- actuator effort/current;
- wheel state;
- body velocity;
- body acceleration;
- contact state;
- end-effector pose;
- actuator temperature/health;
- battery/power state;
- mechanical fault indicators.

The brain must be able to distinguish:

```text
commanded movement
        vs
observed movement
```

A mismatch is evidence of possible slip, obstruction, actuator failure, communication failure, or model error.

## 13. Action-result attribution

Embodied state must support the cognitive loop:

```text
intent
 ↓
action proposal
 ↓
command
 ↓
observed body response
 ↓
world response
 ↓
outcome
```

For example, if Novi commands forward motion but measured velocity remains near zero, the brain must receive an explicit discrepancy rather than assuming the action succeeded.

This is critical for learning, recovery and trustworthy behavior.

## 14. Spatial association

Every spatially grounded observation should be associable with the current embodied state.

Example:

```text
camera detection
  ↓
camera frame
  ↓
TF lookup at observation time
  ↓
body pose at observation time
  ↓
world-frame estimate
  ↓
tracked entity
```

If the transform cannot be obtained with acceptable temporal validity, the observation must remain locally grounded and be marked as insufficient for global spatial reasoning.

## 15. Active embodiment

Novi's body can be used to improve perception.

The brain may request actions such as:

- rotate toward a sound;
- move camera/head orientation;
- change viewpoint;
- approach an object to improve visual resolution;
- circle an object to disambiguate geometry;
- stop movement to improve sensor quality.

These are **active-perception proposals**, not direct motor commands. They pass through normal planning, governance and safety.

This creates a closed loop:

```text
uncertainty
   ↓
information-gain estimate
   ↓
active-perception proposal
   ↓
safe action
   ↓
new observation
   ↓
reduced uncertainty
```

## 16. Simulation and digital validation

The spatial/proprioceptive layer must be testable in simulation before physical deployment.

Isaac Sim currently supports RGB/RGB-D cameras, 2D/3D RTX LiDAR, IMU, contact, radar and ultrasonic sensor types and provides ROS 2 integration. citeturn0search1

Isaac Sim also documents ROS 2 workflows combining joint states, TF, odometry, LiDAR, clock and velocity commands with Nav2, providing a useful reference pattern for Novi's simulated embodied-state pipeline. citeturn0search5

Required simulation tests include:

- stationary robot;
- constant velocity;
- rotation;
- acceleration/deceleration;
- wheel slip;
- sensor dropout;
- delayed sensor;
- noisy IMU;
- incorrect extrinsics;
- localization loss;
- relocalization;
- dynamic obstacles;
- contact events;
- command/response mismatch;
- clock perturbation;
- replay determinism.

## 17. Hardware validation

Physical validation must include:

### Static

- frame-tree correctness;
- sensor extrinsics;
- encoder zero points;
- IMU orientation;
- stationary drift;
- timestamp integrity.

### Dynamic

- straight-line motion;
- controlled rotations;
- repeated trajectories;
- acceleration/deceleration;
- surface changes;
- controlled wheel slip;
- obstacle interaction.

### Fault injection

- IMU disconnect;
- camera disconnect;
- encoder disconnect;
- stale TF;
- delayed measurements;
- conflicting estimates;
- localization loss;
- compute overload.

No learned model should be credited with solving an estimation problem until its benefit has been demonstrated against a deterministic/reference baseline.

## 18. NVIDIA technology candidates

NVIDIA technologies that may contribute to this layer include:

- Isaac Sim for simulated sensors, physics and ROS 2 integration;
- Isaac ROS Visual SLAM for visual-inertial localization;
- Isaac ROS Nvblox for spatial reconstruction and navigation-oriented representations;
- Isaac ROS sensor-processing and NITROS infrastructure for accelerated data paths.

These are **candidate implementation components**, not architectural requirements. Each adoption requires a version/platform compatibility check, benchmark, integration test and ADR.

## 19. Resource and latency classes

The embodied-state path should be divided into:

| Path | Purpose | Requirement |
|---|---|---|
| Critical fast state | controller/safety consumers | bounded latency, predictable availability |
| Local motion | navigation and local planning | low latency, continuous |
| Spatial fusion | world-model updates | freshness + uncertainty |
| Cognitive | reasoning/context | asynchronous where possible |
| Historical | replay/learning | durable, not real-time |

The brain must never make a high-latency model call a prerequisite for basic body-state availability.

## 20. Failure policy

When a sensor or estimator fails:

```text
failure detected
      ↓
quality reduced
      ↓
state marked degraded
      ↓
alternative estimator/source evaluated
      ↓
capability degraded or recovered
      ↓
brain informed
```

The estimator must not silently continue publishing apparently healthy state after its validity assumptions have failed.

Safety-critical reactions remain outside this document and must be governed by the dedicated safety architecture.

## 21. Security and integrity

Spatial state is security-sensitive because false pose or body state can cause physical harm.

Controls must include:

- authenticated software/artifacts;
- protected configuration;
- calibration integrity;
- source identity;
- timestamp validation;
- replay detection where relevant;
- bounded acceptance of external localization sources;
- auditability of estimator configuration;
- isolation of untrusted inputs.

## 22. Required contracts

The implementation must eventually expose canonical contracts for:

- `EmbodiedState`;
- `PoseEstimate`;
- `VelocityEstimate`;
- `JointStateEstimate`;
- `LocalizationStatus`;
- `TransformSnapshot`;
- `SensorCalibration`;
- `StateQuality`;
- `StateDiscrepancy`;
- `SpatialEvidence`.

These must reference the canonical system contracts defined by the system architecture and must not create incompatible duplicate semantics.

## 23. Required ADRs

At minimum:

- spatial-estimation backend;
- visual-inertial localization backend;
- lidar localization strategy;
- estimator fusion architecture;
- transform/frame authority;
- calibration storage/versioning;
- time synchronization hardware/software strategy;
- simulation ground-truth policy;
- state-estimate publication rates;
- learned-vs-deterministic state estimation.

## 24. Acceptance criteria

This specification is not implementation-complete until Novi can demonstrate:

1. every spatial estimate has timestamp, frame and provenance;
2. the frame tree is machine-validatable;
3. stale transforms are detected;
4. localization confidence/state is explicit;
5. IMU and encoder inputs can be fused or independently evaluated;
6. visual and geometric localization can be compared;
7. sensor dropout is detectable;
8. localization loss is detectable;
9. relocalization is observable;
10. commanded-vs-observed motion discrepancies are represented;
11. active perception can request additional observations;
12. simulation and replay cover the failure cases above;
13. physical validation can compare estimates against a reference;
14. uncertainty reaches downstream consumers;
15. no estimator can directly bypass safety/control boundaries.

## 25. Open questions

The following remain deliberate decisions rather than undocumented assumptions:

- exact robot morphology and locomotion type;
- final sensor suite;
- exact localization/fusion implementation;
- whether hardware timestamping/PTP is required at Stage 1;
- exact ROS 2 state-estimation package selection;
- final NVIDIA Isaac ROS components;
- whether a learned state estimator is justified;
- target state-update rates;
- physical reference system for ground-truth evaluation.

These must be resolved through requirements, benchmarks and ADRs once the robot hardware and Stage-1 workload are frozen.

## 26. Design conclusion

Novi's embodied intelligence depends on maintaining a continuously updated relationship between **self, space, motion and observation**.

The spatial/proprioceptive layer therefore acts as the bridge between:

```text
senses
  ↓
where am I?
  ↓
what is my body doing?
  ↓
where are things relative to me?
  ↓
what changed because I acted?
  ↓
what do I believe about the physical world?
```

The intended result is not merely localization. It is **embodied state awareness**: Novi can perceive the world, know where he is within it, know what his body is doing, detect when his expectations are wrong, deliberately change his viewpoint, and feed those facts continuously into cognition, memory, planning and behavior.

## 27. Validation references

Primary NVIDIA references used for this specification:

- Isaac Sim ROS 2 Reference Architecture — sensors and ROS 2 bridge. citeturn0search1
- Isaac Sim ROS 2 Transform Trees and Odometry — frame trees, articulation transforms and odometry. citeturn0search0
- Isaac Sim IMU / RL controller workflow — IMU observations and body-frame requirements. citeturn0search3turn0search6
- Isaac Sim ROS 2 publish-rate documentation — independent sensor rates and simulation timing. citeturn0search4
- Isaac Sim ROS 2 integrated navigation workflow — joint states, TF, odometry, LiDAR and Nav2 integration. citeturn0search5

These references validate NVIDIA platform capabilities and documented integration patterns. They do **not** constitute evidence that a given Novi implementation is correct. Novi must produce its own benchmark and validation evidence before adopting any candidate implementation.