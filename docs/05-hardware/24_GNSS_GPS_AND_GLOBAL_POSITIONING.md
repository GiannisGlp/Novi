# 24 — GNSS, GPS and Global Positioning

## Status

**ARCHITECTURE — HIGH LEVEL / V1**

## Purpose

Define Novi's hardware-level requirement for outdoor global positioning and its relationship to local navigation, mapping and spatial memory.

## 1. Core Requirement

Novi should include a GNSS receiver capable of providing global position when outdoors.

GPS is one constellation; the preferred architecture is multi-constellation GNSS where practical, potentially including:

- GPS;
- Galileo;
- GLONASS;
- BeiDou.

The exact receiver will be selected later through component benchmarking.

## 2. GNSS Is Not the Navigation System

```text
GNSS
  ↓
global reference
  ↓
state estimation
  ↕
LiDAR / cameras / IMU / odometry
  ↓
local pose + map
  ↓
spatial memory
```

GNSS should complement local localization rather than replace SLAM or sensor fusion.

## 3. Required Data

The GNSS subsystem should expose, where supported:

- latitude;
- longitude;
- altitude;
- fix type;
- estimated position accuracy;
- velocity;
- heading/course where valid;
- satellite/constellation information;
- correction status;
- receiver health;
- timestamps;
- diagnostic state.

## 4. Accuracy

The architecture must preserve reported uncertainty.

Potential operating classes:

```text
coarse outdoor position
standard GNSS
augmented/corrected GNSS
RTK-level positioning (optional)
```

RTK is not assumed necessary for V1. It should be introduced only if prototype requirements demonstrate that ordinary multi-constellation GNSS plus local localization is insufficient.

## 5. Antenna

The final design must consider:

- antenna placement;
- sky visibility;
- robot body occlusion;
- multipath;
- electromagnetic interference;
- cable length;
- grounding;
- enclosure effects;
- weather exposure for outdoor use.

The antenna location must be designed together with cameras, LiDAR, displays and radio antennas.

## 6. Time

GNSS may provide useful timing information, but Novi's canonical event architecture must retain its established timestamp model.

Acquisition time, receive time and synchronization quality must remain distinguishable.

## 7. Indoor Behavior

GNSS loss indoors is expected.

The robot must transition to local positioning without treating GNSS absence as a system failure.

```text
GNSS available
   ↓
global + local fusion

GNSS unavailable
   ↓
local SLAM / odometry / perception
```

## 8. Outdoor Place Memory

GNSS should provide a global anchor for outdoor spatial memory:

```text
GNSS position
      ↓
place candidate
      ↓
local map
      ↓
visit episode
      ↓
spatial memory
```

This allows Novi to remember that a physically visited place corresponds to a global geographic region.

## 9. GNSS + Local Map Alignment

Where reliable global position is available, Novi may associate a local SLAM map with a global geographic frame.

The transform must be versioned and retain uncertainty.

Historical memories must remain linked to the map/global-frame version that produced them.

## 10. Multipath and Urban Conditions

GNSS can degrade around:

- buildings;
- reflective surfaces;
- trees;
- bridges;
- narrow streets;
- other obstructions.

The receiver's reported accuracy must be treated as evidence, not absolute truth. Novi should use independent localization sources to detect implausible jumps.

## 11. Loss and Recovery

The subsystem should emit explicit state transitions:

```text
healthy
↓
degraded
↓
no_fix
↓
recovering
↓
healthy
```

A GNSS outage must not erase previous spatial memory.

## 12. Spoofing / Integrity

Outdoor autonomous operation should consider GNSS integrity risks, including implausible jumps and inconsistent velocity/position.

Novi should compare GNSS against independent local state estimation and flag suspicious discrepancies rather than blindly accepting a position.

Detailed threat modelling belongs in the security architecture.

## 13. Connectivity Independence

Basic GNSS positioning must not require Wi-Fi, Bluetooth or cloud access.

Optional correction services may improve accuracy when available, but loss of those services must not break core outdoor operation.

## 14. Jetson Integration

The final receiver must expose a stable local interface compatible with Novi's compute architecture. Candidate interfaces may include USB, UART, Ethernet or another appropriate hardware interface.

Driver selection must prefer maintained local/open solutions where practical.

## 15. Power

The GNSS receiver and antenna subsystem must be included in Novi's power budget and monitored where useful.

Power-saving modes may be used when GNSS is unnecessary, subject to wake-up and reacquisition requirements.

## 16. Hardware Placement

GNSS hardware must be coordinated with:

- Wi-Fi/Bluetooth radios;
- cameras;
- LiDAR;
- microphone array;
- speakers;
- displays;
- RGB lighting;
- compute;
- battery;
- motor controllers.

The design should minimize electromagnetic and physical interference.

## 17. Privacy

Global location can be highly sensitive.

GNSS-derived location must be subject to Novi's spatial-memory privacy, retention, deletion and synchronization policies.

## 18. Diagnostics

Monitor at minimum where supported:

- fix state;
- position accuracy;
- satellite/constellation quality;
- correction state;
- receiver health;
- timestamp quality;
- implausible jumps;
- interface errors;
- antenna/receiver faults where detectable.

## 19. Candidate Technology Evaluation

The architecture must compare available open/local GNSS receivers and software stacks rather than locking to a vendor at this stage.

Evaluation criteria:

- multi-constellation support;
- accuracy;
- update rate;
- cold/warm start;
- power;
- antenna requirements;
- interface;
- Linux/Jetson compatibility;
- driver quality;
- local operation;
- correction support;
- physical size;
- cost;
- availability;
- long-term support.

## 20. Testing

Test:

- open-sky positioning;
- partial obstruction;
- urban environments;
- stationary accuracy;
- moving accuracy;
- GNSS loss;
- reacquisition;
- multipath;
- implausible jumps;
- time quality;
- local-map fusion;
- indoor transition;
- offline operation;
- power-saving/recovery;
- long-duration outdoor operation.

## 21. Architectural Invariants

1. GNSS is a global positioning source, not a complete navigation system.
2. GPS is not the only constellation considered.
3. GNSS uncertainty is preserved.
4. GNSS loss must not break local autonomy.
5. GNSS does not require Internet connectivity for basic operation.
6. Global and local coordinate frames remain distinct.
7. GNSS-derived memories retain provenance.
8. Suspicious GNSS behavior must be cross-checked against independent evidence.
9. RTK is optional and evidence-driven.
10. Location data remains subject to privacy and deletion policy.
11. Exact hardware selection requires prototype benchmarking.

## 22. Final Principle

> **GNSS gives Novi a relationship to the global world; SLAM and sensor fusion give Novi an understanding of the local world. Spatial memory connects the two.**
