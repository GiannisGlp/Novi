# 05 — Hardware

## High-Level Description

This folder defines the physical hardware architecture for Novi: compute, sensing, perception hardware, audio, displays, lighting, actuation interfaces, power, thermal monitoring, safety, connectivity, storage, and hardware diagnostics.

The current documents are intentionally **high-level architecture specifications**. They establish what Novi needs and why, while leaving detailed component selection, electrical design, mechanical CAD, PCB design, wiring, thermal simulation, firmware, driver configuration, calibration procedures, BOMs, and validation plans for later engineering phases.

## Design Principles

1. **Local-first:** Novi's physical operation must not depend on Wi-Fi, Bluetooth, or cloud services.
2. **Sensor fusion:** no single sensor should unnecessarily become a single point of failure for perception.
3. **Redundancy where safety requires it:** safety-critical capabilities should have independent or complementary sensing where practical.
4. **Self-awareness:** Novi must monitor the health, availability, calibration state, temperature, power and performance of its own hardware.
5. **Graceful degradation:** loss of a non-critical sensor must reduce capability rather than unnecessarily stopping the robot.
6. **Replaceable interfaces:** hardware components should communicate through stable interfaces so components can be upgraded without redesigning the entire software architecture.
7. **Open/local preference:** prefer open-source drivers, protocols and locally executable software; vendor-specific components are acceptable when they materially improve the system.
8. **Jetson optimization:** the initial compute target is NVIDIA Jetson AGX Orin 64GB.
9. **Privacy by hardware architecture:** cameras, microphones and biometric-capable sensors must have explicit privacy states and hardware/software control paths.
10. **Safety is independent of the LLM:** physical safety mechanisms must not depend on generative reasoning.

## Planned Hardware Documents

| Document | Scope | Status |
|---|---|---|
| `00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md` | Complete physical-system architecture and hardware boundaries | Current |
| `01_COMPUTE_AND_ACCELERATION.md` | Jetson, storage, accelerators and compute interfaces | High-level |
| `02_VISION_AND_CAMERA_SYSTEM.md` | RGB, depth, IR and camera placement concepts | High-level |
| `03_THERMAL_SENSING_AND_ENVIRONMENTAL_TEMPERATURE.md` | Thermal camera and ambient temperature sensing | High-level |
| `04_LIDAR_DEPTH_AND_PROXIMITY.md` | LiDAR, ToF, ultrasonic and proximity sensing | High-level |
| `05_IMU_ODOMETRY_AND_MOTION_SENSING.md` | IMU, encoders and motion estimation hardware | High-level |
| `06_AUDIO_INPUT_AND_MICROPHONE_ARRAY.md` | Microphones, beamforming and direction-of-arrival hardware | High-level |
| `07_AUDIO_OUTPUT_AND_SPEAKERS.md` | Speaker system and audio output | High-level |
| `08_DISPLAYS_AND_EYE_SYSTEM.md` | ~5-inch face display and body display | High-level |
| `09_RGB_LIGHTING_AND_STATUS_OUTPUT.md` | Multi-zone RGB lighting and semantic states | High-level |
| `10_ACTUATORS_MOTORS_AND_FEEDBACK.md` | Motors, actuators, encoders, current/torque feedback | High-level |
| `11_POWER_BATTERY_AND_POWER_MANAGEMENT.md` | Battery, BMS, rails and power telemetry | High-level |
| `12_INTERNAL_THERMAL_MANAGEMENT.md` | Compute/electronics/motor/battery thermal monitoring and cooling | High-level |
| `13_ENVIRONMENTAL_SENSORS.md` | Humidity, air quality, CO2, particulate, ambient light and related sensors | High-level |
| `14_CONTACT_TACTILE_AND_FORCE_SENSING.md` | Bumpers, contact, force and tactile sensing | High-level |
| `15_HARDWARE_SAFETY_SYSTEM.md` | Emergency stop, hardware interlocks and independent safety mechanisms | High-level |
| `16_CONNECTIVITY_AND_LOCAL_INTERFACES.md` | Wi-Fi, Bluetooth, USB, Ethernet, CAN, serial and other local interfaces | High-level |
| `17_STORAGE_AND_DATA_RESILIENCE.md` | Local storage, endurance, health and recovery | High-level |
| `18_HARDWARE_DIAGNOSTICS_AND_HEALTH.md` | Self-monitoring and fault detection | High-level |
| `19_SENSOR_CALIBRATION_AND_TIME_SYNC.md` | Calibration, synchronization and measurement quality | High-level |
| `20_SENSOR_FUSION_HARDWARE_REQUIREMENTS.md` | Cross-sensor timing, synchronization and fusion requirements | High-level |
| `21_MECHANICAL_AND_PHYSICAL_ARCHITECTURE.md` | Chassis, mounting, serviceability, cable routing and physical constraints | High-level |
| `22_HARDWARE_PRIVACY_CONTROLS.md` | Camera/microphone indicators, physical controls and privacy states | High-level |
| `23_HARDWARE_VALIDATION_AND_TESTING.md` | Hardware verification, environmental and fault testing | High-level |

## Current Hardware Baseline

Novi is expected to include, at minimum:

- NVIDIA Jetson AGX Orin 64GB as the initial compute target;
- multiple RGB cameras;
- depth sensing;
- environmental thermal camera;
- internal compute/electronics/battery/motor thermal monitoring;
- LiDAR;
- IMU;
- wheel/actuator encoders where applicable;
- microphone array;
- multiple speakers;
- approximately 5-inch face/eye display;
- approximately 5–7-inch body display for occasional detailed information;
- multi-zone RGB lighting;
- motor/actuator feedback;
- battery and power telemetry;
- proximity sensing;
- contact/bump/force sensing;
- environmental sensing where justified;
- local storage;
- Wi-Fi and Bluetooth as optional capabilities;
- hardware safety mechanisms independent of network connectivity and the AI model.

## Important Separation: External vs Internal Thermal Sensing

Novi requires two different thermal domains:

```text
ENVIRONMENTAL THERMAL SENSING
thermal camera / ambient temperature
        ↓
understand hot/cold objects and surroundings

INTERNAL THERMAL MONITORING
Jetson / battery / motors / electronics
        ↓
protect Novi itself
```

They must not be conflated.

## Future Detailed Engineering

Later hardware work must define:

- exact component candidates and alternatives;
- electrical specifications;
- voltage/current requirements;
- CSI/USB/PCIe/CAN/I2C/SPI/UART interfaces;
- connector and cable requirements;
- clock synchronization;
- thermal budgets;
- power budgets;
- mechanical dimensions;
- mounting locations;
- sensor fields of view;
- calibration targets and procedures;
- firmware and driver requirements;
- BOM and sourcing;
- repair/replacement strategy;
- manufacturing constraints;
- EMI/EMC considerations;
- environmental operating limits;
- reliability and lifecycle requirements.

Detailed hardware choices must be benchmarked against the actual Novi prototype rather than selected solely from datasheets.
