# 32 — Compute Platform Comparison: Jetson AGX Orin 64GB vs Jetson Thor T5000

**Status:** Architecture decision research baseline  
**Priority:** P0  
**Owner:** System Architecture / Hardware / Brain  
**Date:** 2026-08-18  
**Decision state:** No final hardware purchase decision yet

## 1. Executive conclusion

Novi should evaluate two fundamentally different deployment profiles:

1. **Mobile Novi:** Jetson AGX Orin 64GB as the preferred high-capability mobile candidate.
2. **Stationary / heavy-compute Novi:** Jetson Thor T5000 as the preferred candidate when wall power, a large battery, or a substantially larger chassis is acceptable.

The reason is not simply AI TOPS. It is the combined system cost of compute, memory, power, thermal management, battery mass, chassis volume and motor/energy consequences.

NVIDIA currently specifies AGX Orin 64GB at up to 275 sparse INT8 TOPS and 15–60W configurable power. Jetson Thor T5000 is specified at up to 2070 FP4 sparse TFLOPS, 128GB memory and 40–130W configurable power. NVIDIA describes Thor as a physical-AI platform designed for generative AI, multimodal sensing and advanced robotics. [Sources: NVIDIA Jetson Orin; NVIDIA Jetson Thor; NVIDIA Jetson modules.]

**Current recommendation:** Do not lock Novi's mobile robot to Thor until the complete robot energy model demonstrates that an 8–10 hour battery target remains practical. Thor should simultaneously be treated as a serious stationary/plugged-in Novi option, where its compute advantage is not paid for with battery mass.

---

## 2. Primary-source facts

| Attribute | Jetson AGX Orin 64GB | Jetson Thor T5000 |
|---|---:|---:|
| Architecture | NVIDIA Ampere | NVIDIA Blackwell |
| Memory | 64GB LPDDR5 | 128GB LPDDR5X |
| AI headline | 275 sparse INT8 TOPS | 2070 FP4 sparse TFLOPS |
| Power range | 15–60W | 40–130W |
| CPU | 12-core Arm Cortex-A78AE | 14-core Arm Neoverse V3AE |
| GPU | 2048 CUDA cores / 64 Tensor cores | 2560 CUDA cores / 5th-gen Tensor cores |
| GPU special capability | Ampere Tensor cores, 2x NVDLA v2 | Blackwell Transformer Engine, FP4, MIG |
| Memory bandwidth | ~204.8GB/s | ~273GB/s |
| Developer kit MSRP | $3,499 | $5,499 |
| Production module reference | $2,999 at 1KU+ | $4,999 at 1KU+ |
| Mobile suitability | **Excellent** | **Conditional** |
| Stationary AI suitability | Very good | **Excellent** |

NVIDIA's current published comparison lists 275 TOPS for AGX Orin and 2070 FP4 sparse TFLOPS for Thor. The metrics are not directly interchangeable: TOPS and FP4 TFLOPS use different precision/operation definitions. Do not multiply the numbers to claim a literal performance ratio. NVIDIA separately states that Thor can provide up to 7.5x higher AI compute and 3.5x higher energy efficiency than AGX Orin for the workloads measured by NVIDIA.

Sources:
- https://www.nvidia.com/en-gb/autonomous-machines/embedded-systems/jetson-orin/
- https://www.nvidia.com/en-gb/autonomous-machines/embedded-systems/jetson-thor/
- https://developer.nvidia.com/embedded/faq

---

## 3. What the memory difference means for Novi

### AGX Orin 64GB

64GB is a major step above the 16GB NX candidate and should be considered a serious local-AI platform. It can support perception, ROS 2, navigation, memory services, multiple models and a sizeable local language/vision workload without immediately forcing every model to be tiny.

### Thor 128GB

Thor's 128GB is a different class of headroom. It is particularly valuable when Novi wants simultaneous:

- LLM reasoning;
- VLM perception/reasoning;
- VLA/action models;
- multimodal sensor processing;
- memory/context retrieval;
- multiple model replicas/concurrency;
- large KV caches;
- higher-resolution vision;
- future world-model or embodied-AI workloads.

The practical advantage is not merely fitting one larger model. It is fitting **multiple concurrent workloads without forcing aggressive eviction and quantization**.

---

## 4. AI model capability comparison

NVIDIA's current public benchmarks provide an unusually useful direct comparison. Under NVIDIA's benchmark configuration, both platforms were measured at MAXN power mode with sequence length 2048, output sequence length 128 and max concurrency 8.

| Workload | AGX Orin | Thor | Thor advantage in NVIDIA test |
|---|---:|---:|---:|
| Llama 3.1 8B | 112.33 tok/s | 150.8 tok/s | ~1.34x |
| Llama 3.3 70B | 7.38 tok/s | 12.64 tok/s | ~1.71x |
| Qwen3 30B-A3B | 76.69 tok/s | 226.42 tok/s | ~2.95x |
| Qwen3 32B | 16.84 tok/s | 79.1 tok/s | ~4.70x |
| DeepSeek-R1-Distill-Qwen-7B | 180.41 tok/s | 304.76 tok/s | ~1.69x |
| DeepSeek-R1-Distill-Qwen-32B | 16.96 tok/s | 82.63 tok/s | ~4.87x |
| Qwen2.5-VL-3B | 216 tok/s | 356.86 tok/s | ~1.65x |
| Qwen2.5-VL-7B | 154.02 tok/s | 252 tok/s | ~1.64x |
| Llama 3.2 11B Vision | 44.22 tok/s | 69.63 tok/s | ~1.57x |
| GR00T N1 | 18.5 tok/s | 46.7 tok/s | ~2.52x |
| GR00T N1.5 | 15.2 tok/s | 41.5 tok/s | ~2.74x |

These are NVIDIA measurements, not guarantees for Novi. Real performance depends on model build, quantization, context length, sensor load, ROS/DDS traffic, concurrency, thermal state and power mode.

Source: NVIDIA Technical Blog and Jetson Benchmarks.

---

## 5. Model classes Novi should consider

### AGX Orin 64GB is appropriate for

- small/medium LLMs such as Llama 3.1/3.2 8B-class models;
- Qwen 7B/14B-class reasoning workloads after appropriate quantization;
- 7B-class VLMs;
- DeepSeek distilled 7B/14B/32B-class workloads where latency is acceptable;
- conventional object detection, segmentation and pose models;
- depth estimation;
- visual odometry and SLAM;
- speech recognition/TTS;
- local embedding/reranking models;
- selected VLA models after profiling;
- multiple small models concurrently.

The 64GB memory pool gives substantially more freedom than Orin NX 16GB.

### Thor is appropriate for

All of the above, with significantly more headroom for:

- larger LLMs;
- 30B/32B-class models at useful rates;
- 70B-class models at lower but usable generation rates, subject to quantization/context;
- larger VLMs;
- multiple simultaneous VLM + LLM workloads;
- VLA models such as NVIDIA GR00T N1/N1.5;
- high-concurrency multimodal inference;
- agentic AI pipelines;
- larger KV caches;
- future physical-AI/world-model workloads.

Thor's Blackwell Transformer Engine and FP4 support are particularly relevant to generative AI. NVIDIA also demonstrates speculative decoding and multi-model concurrency on Thor.

Sources: NVIDIA Jetson Thor technical blog and Jetson Benchmarks.

---

## 6. Important model caveat

"Can run" must not be interpreted as "can run well."

For every candidate model Novi must measure:

```text
weights memory
KV-cache memory
activation memory
startup time
TTFT
TPOT
p50/p95/p99 latency
power
GPU utilization
CPU utilization
thermal behavior
concurrency
sensor interference
```

A model may technically load while being unsuitable for a responsive robot.

---

## 7. Mobile 8–10 hour battery target

The 8–10 hour requirement must be calculated from **average whole-robot electrical power**, not compute TDP alone.

The energy equation is:

```text
Required nominal battery energy
    = average robot load × desired hours
      ÷ usable-depth factor
      ÷ conversion efficiency
```

For this study use:

- 80% usable battery energy target;
- 90% aggregate conversion/distribution efficiency as a preliminary design factor;
- therefore approximately 72% of nameplate Wh is treated as usable at the robot bus.

This is a planning assumption, not a battery certification value.

### Example A — AGX Orin mobile robot

Assume:

```text
Compute:              50W average
Sensors/network:      30W
MCU/control/etc:       10W
Motors/actuation:      60W average
──────────────────────────────
Robot average:       150W
```

For 8 hours:

```text
150 × 8 = 1,200Wh delivered
1,200 / 0.72 ≈ 1,667Wh nominal
```

For 10 hours:

```text
150 × 10 = 1,500Wh delivered
1,500 / 0.72 ≈ 2,083Wh nominal
```

So an initial **2.0–2.5kWh battery class** is a reasonable design envelope for a relatively efficient AGX Orin mobile robot.

### Example B — Thor mobile robot

Assume a much heavier compute envelope:

```text
Compute:              100W average
Sensors/network:       40W
MCU/control/etc:       10W
Motors/actuation:     100W average
──────────────────────────────
Robot average:       250W
```

For 8 hours:

```text
250 × 8 = 2,000Wh delivered
2,000 / 0.72 ≈ 2,778Wh nominal
```

For 10 hours:

```text
250 × 10 = 2,500Wh delivered
2,500 / 0.72 ≈ 3,472Wh nominal
```

This suggests a **3–4kWh battery class** before accounting for particularly aggressive motor duty cycles or cold-weather derating.

These are scenarios, not final battery selections.

---

## 8. Battery examples

### 24V 100Ah LiFePO4

Nominal energy:

```text
25.6V × 100Ah = 2.56kWh
```

At the planning 72% usable system factor:

```text
2.56 × 0.72 ≈ 1.84kWh delivered
```

This is approximately:

- 12.3h at a hypothetical 150W average load;
- 7.4h at a hypothetical 250W average load.

Therefore one 24V 100Ah pack is a plausible starting point for an efficient Orin robot, but it is **not enough for a 250W Thor robot to guarantee 8–10 hours**.

Current UK examples range widely: Eco-Worthy lists a 24V 100Ah pack around £380, Renogy currently lists its 24V 100Ah Core battery around £700, and higher-end products can cost substantially more. These are market examples, not a Novi-selected battery.

### 48V 50Ah LiFePO4

Nominal energy:

```text
51.2V × 50Ah = 2.56kWh
```

The same energy is available at roughly half the current of a 24V system, which is attractive for larger motor loads.

Current UK examples range from roughly £420–£1,285 depending on manufacturer/specification.

For a Thor-class mobile robot, **48V is attractive** because higher bus voltage reduces current for the same power and therefore reduces cable/connector losses and conductor size.

---

## 9. Battery recommendation by platform

| | AGX Orin mobile | Thor mobile |
|---|---:|---:|
| Starting battery class | 24V 100Ah / 2.56kWh | 48V 50–80Ah / 2.56–4.1kWh |
| Target nominal energy for 8h | ~1.7kWh minimum scenario | ~2.8kWh minimum scenario |
| Target nominal energy for 10h | ~2.1kWh minimum scenario | ~3.5kWh minimum scenario |
| Preferred design margin | 2.0–2.5kWh | 3.5–4.5kWh |
| Battery bus | 24V or 48V | **48V preferred** |
| Battery chemistry | LiFePO4 | LiFePO4 |

Final selection requires measured motor duty cycle.

---

## 10. Power architecture — mobile AGX Orin

Recommended architecture:

```text
24/48V LiFePO4 battery
        │
        ├── main fuse
        │
        ├── contactor / precharge
        │
        ├── motor controller bus
        │
        └── isolated/non-isolated DC/DC
                 │
                 ├── Jetson input rail
                 ├── sensors
                 └── networking
```

The Jetson compute path should not share uncontrolled transient power with motors.

Motor acceleration can create substantial voltage/current transients; power integrity must therefore be designed around the motor controller, not merely the Jetson's average wattage.

---

## 11. Power architecture — mobile Thor

Thor's higher power changes the architecture:

```text
48V battery
    │
    ├── high-current motor bus
    │
    ├── compute DC/DC
    │       └── 7–20V HV input capability
    │
    ├── sensor DC/DC
    │
    └── protected auxiliary bus
```

The T5000 module specifies a 7–20V SYS_VIN_HV input plus 5V and 3.3V rails supplied by the carrier board. A Thor carrier therefore has to perform the necessary power conversion/regulation.

Source: NVIDIA T5000 module datasheet.

---

## 12. Thermal architecture — AGX Orin

AGX Orin 64GB is configurable up to 60W. A mobile implementation should use an active thermal solution if the goal is sustained high AI load.

Required:

- thermal transfer plate / heatsink;
- heatpipe or equivalent conduction path;
- fan or equivalent active airflow;
- controlled intake/exhaust;
- temperature sensors;
- fan control;
- dust management;
- thermal throttling telemetry;
- enclosure airflow design.

NVIDIA publishes an AGX Orin Thermal Design Guide; carrier vendors also provide active/passive thermal assemblies.

---

## 13. Thermal architecture — Thor

Thor is materially harder thermally.

At 130W compute, the robot has to continuously remove roughly 130W of heat from the compute subsystem—plus carrier losses and nearby electronics.

That can require:

- large heatsink/heatpipe;
- high-airflow blower;
- carefully designed ducting;
- enclosure thermal path;
- or liquid cooling for sustained high-power deployments.

NVIDIA provides a dedicated Jetson Thor Series Thermal Design Guide. Connect Tech also offers active/passive and liquid-cooling solutions for Thor/Orin-class modules.

For a stationary robot, this becomes much easier because the enclosure can be larger and the power budget is not constrained by battery mass.

---

## 14. Developer kit vs production module

This distinction matters.

### Development

AGX Orin Developer Kit:

- reference carrier;
- integrated module;
- thermal solution;
- easy prototyping;
- current NVIDIA price: $3,499.

Thor Developer Kit:

- reference carrier;
- T5000;
- integrated 1TB NVMe;
- Wi-Fi 6E/Bluetooth;
- integrated thermal solution;
- current NVIDIA price: $5,499.

### Production

For the actual robot, we should eventually use:

```text
module
+
custom/industrial carrier board
+
robot-specific power
+
robot-specific thermal system
+
robot-specific I/O
```

NVIDIA's current volume reference prices are $2,999 for AGX Orin 64GB and $4,999 for T5000 at 1KU+, but these are not single-unit UK retail prices.

---

## 15. Carrier-board options

### AGX Orin

Connect Tech offers:

- Forge;
- Rogue;
- Rogue-RX.

The Forge supports 10–36V DC input and multiple NVMe/10GbE/camera interfaces. Rogue is a smaller 12V design. These are examples of production-oriented carrier architecture rather than mandatory Novi choices.

### Thor

Connect Tech offers:

- Gauntlet;
- Rogue-T5.

Rogue-T5 supports 12V input, multiple 10GbE interfaces, 2.5GbE, CAN, NVMe and camera ecosystems. Gauntlet supports extensive camera and networking expansion.

For the first physical prototype, the NVIDIA developer kit is preferable for development; for the production robot, select a carrier based on sensor/robot I/O requirements.

---

## 16. Sensor requirements for either platform

The compute platform does not replace the sensors.

Novi's first serious autonomous robot should plan for:

### Core

- IMU;
- wheel encoders;
- motor current/temperature feedback;
- one or more cameras;
- emergency-stop input;
- battery voltage/current/SOC.

### Recommended autonomy perception

- stereo/depth camera;
- RGB camera;
- optional 2D/3D LiDAR;
- optional wide-angle/side/rear cameras.

Thor has substantially more camera and sensor-ingestion headroom. NVIDIA specifies support for up to 20 USB/HSB cameras, up to 6 MIPI cameras through 16 lanes, and up to 32 cameras using virtual channels in the Thor specification, subject to configuration. AGX Orin also has substantial MIPI CSI-2 capability but is less generous for very large multimodal sensor graphs.

This matters for a future Novi robot with multiple cameras and high-rate perception.

---

## 17. Safety architecture remains separate

Neither platform should directly own the final physical safety decision.

Recommended architecture:

```text
             AGX Orin / Thor
                    │
        perception / cognition / planning
                    │
             ActionProposal
                    │
             Safety/Authorization
                    │
              real-time MCU
                    │
              motor controller
                    │
                  motors
```

The high-performance AI computer can fail, reboot, overheat or become overloaded without removing the independent ability to stop the robot safely.

---

## 18. Pros and cons — AGX Orin 64GB

### Pros

- 64GB unified memory is strong for a mobile robot.
- 15–60W configurable power is much easier to battery-power than Thor.
- Mature Jetson/JetPack/Isaac ROS ecosystem.
- Smaller thermal problem.
- Lower platform cost.
- Excellent perception/robotics performance.
- Strong enough for meaningful local LLM/VLM/VLA experimentation.
- Easier to build a compact 8–10 hour mobile platform.
- Large existing ecosystem of carrier boards and thermal solutions.

### Cons

- 64GB limits the largest simultaneous local models.
- Ampere lacks Thor's native Blackwell FP4/Transformer Engine advantages.
- Larger reasoning models have much lower token throughput.
- More aggressive model quantization/selection may be necessary.
- Less headroom for future multimodal/world-model workloads.
- At sustained 60W it still needs serious cooling.

---

## 19. Pros and cons — Thor

### Pros

- 128GB unified memory.
- Blackwell architecture.
- FP4 and Transformer Engine capabilities.
- Up to 2070 FP4 sparse TFLOPS.
- Strong VLM/LLM/VLA performance.
- Much stronger multi-model concurrency.
- NVIDIA explicitly targets physical AI and humanoid robotics.
- Strong future-proofing for local generative AI.
- Large sensor-ingestion capability.
- MIG can help isolate workloads.
- Much better candidate for a stationary AI robot.

### Cons

- 40–130W module power range.
- 130W compute creates a major thermal problem.
- Higher module/developer-kit cost.
- Higher battery energy requirement.
- Larger power electronics and cooling requirements.
- More difficult compact mobile packaging.
- Greater system complexity.
- A lot of its capability may be wasted if Novi ultimately runs small models.
- High power can indirectly increase motor/battery requirements because the entire robot becomes heavier.

---

## 20. Stationary Novi changes the decision

A permanently powered robot is a completely different optimization problem.

For a stationary Novi:

```text
Mains
 │
 ├── UPS
 │
 ├── protected AC/DC
 │
 └── Thor
       │
       ├── large local models
       ├── VLM
       ├── LLM
       ├── VLA
       ├── memory
       ├── multimodal perception
       └── high-concurrency AI
```

In this configuration, Thor becomes significantly more attractive.

The 130W compute requirement is relatively small compared with the energy available from mains power, while the 128GB memory and Blackwell acceleration can be exploited continuously.

A UPS should still be used so that power loss becomes a controlled shutdown/safe-state event rather than an uncontrolled crash.

---

## 21. Stationary Thor recommendation

For a stationary Novi, I would seriously consider:

**Jetson AGX Thor Developer Kit during development → T5000 + production carrier for deployment.**

Potential uses:

- companion robot with rich conversation;
- persistent multimodal memory;
- high-quality VLM perception;
- larger local reasoning models;
- VLA experimentation;
- simulation/robotics research;
- multi-camera perception;
- local agentic workflows;
- future physical-AI research.

This is where Thor's additional compute is easiest to justify.

---

## 22. 8–10 hour mobile recommendation

For the mobile Novi:

### Preferred starting architecture

**AGX Orin 64GB + 24/48V LiFePO4 + independent real-time MCU.**

Design target:

```text
2.0–2.5kWh battery class
~150W average whole-robot target
24V or 48V electrical architecture
active Jetson cooling
independent motor/safety controller
```

This is not a guarantee of 8–10 hours. The motor duty cycle must be measured.

### Thor mobile

Possible, but only if we accept:

```text
3.5–4.5kWh battery class
48V bus preferred
larger thermal system
larger chassis
higher weight
higher cost
```

If the motor system itself consumes 300–500W average, battery requirements grow rapidly and Thor can force a much larger robot.

---

## 23. Rough system cost envelope — UK

These are planning ranges, not quotations.

### AGX Orin mobile prototype

| Item | Planning range |
|---|---:|
| AGX Orin 64GB dev kit | £2,800–£3,500 |
| 1TB/2TB NVMe if additional | £80–£180 |
| Carrier board for production | £250–£900+ |
| Thermal solution | £50–£300+ |
| 24V/48V LiFePO4 2–2.5kWh | £300–£1,500+ |
| DC/DC + protection | £150–£500 |
| MCU/control electronics | £50–£300 |
| IMU/encoders | £100–£500 |
| cameras/depth | £200–£1,500+ |
| LiDAR, if used | £200–£2,000+ |
| motors/drivers | £300–£1,500+ |
| chassis/mechanics | £300–£1,500+ |
| wiring/connectors/fuses/contactors | £150–£500 |
| **Compute-to-robot prototype subtotal** | **roughly £5k–£15k** |

The range is intentionally broad because motors, LiDAR and mechanical construction dominate the uncertainty.

### Thor mobile prototype

| Item | Planning range |
|---|---:|
| Thor developer kit | £4,500–£6,000+ |
| T5000 production module | ~£4k+ single-unit class; £4,999 NVIDIA 1KU+ reference |
| Production carrier | £500–£1,500+ |
| 1–2TB NVMe | £100–£250 |
| Active/liquid thermal system | £200–£1,000+ |
| 3.5–4.5kWh LiFePO4 | £500–£2,500+ |
| 48V DC/DC/power protection | £250–£800+ |
| MCU/control | £50–£300 |
| sensors | £500–£4,000+ |
| motors/drivers | £500–£2,000+ |
| larger chassis | £500–£2,500+ |
| **rough prototype envelope** | **~£8k–£25k+** |

These figures are planning estimates and must be replaced with supplier quotations before procurement.

---

## 24. Cost evidence currently available

NVIDIA currently lists:

- AGX Orin Developer Kit: **$3,499**;
- AGX Orin 64GB production module: **$2,999 at 1KU+**;
- Jetson AGX Thor Developer Kit: **$5,499**;
- Jetson T5000: **$4,999 at 1KU+**.

A current UK RS listing showed the AGX Orin 64GB Developer Kit at £2,760 ex VAT / £3,312 inc VAT. A current UK Scan listing showed the T5000 module at £3,668.99, although stock/pricing can change.

These numbers show that Thor's premium is real even before the robot's battery and thermal costs are considered.

---

## 25. Energy economics: the key insight

For a mobile robot, the important metric is not:

```text
AI performance / watt of the module
```

It is closer to:

```text
useful autonomous capability
──────────────────────────────
whole-robot watts + battery mass + thermal mass
```

A 130W Thor robot that needs a 4kWh battery, larger motors and a larger chassis can be inferior to a 60W Orin robot if the task does not actually require Thor's additional AI capability.

Conversely, a stationary Thor robot can be superior because battery mass becomes irrelevant.

---

## 26. Decision matrix

| Criterion | AGX Orin 64GB | Thor T5000 |
|---|---:|---:|
| Mobile 8h | **5/5** | 2/5 |
| Mobile 10h | **5/5** | 2/5 |
| Stationary | 4/5 | **5/5** |
| Local LLM | 4/5 | **5/5** |
| Large LLM | 3/5 | **5/5** |
| VLM | 4/5 | **5/5** |
| VLA | 3/5 | **5/5** |
| Multi-model concurrency | 3/5 | **5/5** |
| Memory headroom | 4/5 | **5/5** |
| Power efficiency for small robot | **5/5** | 3/5 |
| Thermal simplicity | **5/5** | 2/5 |
| Hardware cost | **4/5** | 2/5 |
| Ecosystem maturity | **5/5** | 4/5 |
| Future AI headroom | 3/5 | **5/5** |
| Small chassis | **5/5** | 2/5 |
| Physical-AI ambition | 4/5 | **5/5** |

Scores are engineering judgments, not vendor measurements.

---

## 27. Recommended Novi hardware strategy

Do not make one hardware platform define the entire Novi architecture.

Define a hardware capability abstraction:

```text
Novi Runtime
     │
     ├── Mobile Profile
     │      └── AGX Orin 64GB
     │
     ├── Advanced Mobile Profile
     │      └── Thor T5000 (future/large robot)
     │
     └── Stationary Profile
            └── Thor T5000
```

The contracts, cognition architecture, memory architecture, autonomy architecture and safety boundaries remain unchanged.

Only the available compute capability changes.

---

## 28. Required procurement before final selection

Before purchasing production hardware, Novi must obtain actual quotations and datasheets for:

### Compute

- AGX Orin 64GB module/dev kit;
- T5000/dev kit;
- carrier board;
- thermal solution;
- NVMe;
- Wi-Fi/BT;

### Power

- battery;
- BMS;
- charger;
- contactor;
- fuse;
- pre-charge circuit;
- DC/DC converters;
- current/voltage sensors;
- wiring/connectors;

### Robot

- motors;
- motor controllers;
- encoders;
- wheels;
- chassis;
- suspension if required;

### Perception

- camera;
- depth/stereo;
- LiDAR;
- IMU;

### Thermal

- heatsink;
- fan/blower;
- ducts;
- temperature sensors;
- optional liquid cooling for Thor.

---

## 29. Validation plan

The final decision must be based on measurement.

### B1 — Model benchmark

Run the actual intended Novi models on both platforms.

### B2 — Concurrent AI

Run perception + VLM + LLM + memory + ROS simultaneously.

### B3 — Sensor load

Add the intended camera/LiDAR/IMU streams.

### B4 — Full robot

Add localization, navigation, planning and control.

### B5 — Power

Measure average/peak watts at representative duty cycles.

### B6 — Thermal

Run sustained load in the actual enclosure.

### B7 — Battery

Run the physical robot through the intended 8–10 hour duty cycle.

### B8 — Fault injection

Test:

- compute overload;
- thermal throttling;
- power interruption;
- battery low state;
- sensor failure;
- model timeout;
- Jetson reboot;
- MCU/AI communication loss.

---

## 30. Current recommendation

### Mobile Novi

**AGX Orin 64GB is the default candidate.**

Target a 2.0–2.5kWh battery class initially and validate whether the complete robot can sustain 8–10 hours.

### Large mobile Novi

**Thor is a candidate only if the AI workload demonstrably requires it.**

Do not enlarge the robot merely to justify a larger AI computer.

### Stationary Novi

**Thor is strongly recommended for investigation.**

Its 128GB memory, Blackwell architecture, FP4 support and high multi-model throughput make it much more attractive when mains power is available.

### Architecture

Keep Novi hardware-agnostic at the software contract level and expose hardware capabilities through the runtime capability model.

---

## 31. Research sources

Primary sources used for this comparison:

1. NVIDIA — Jetson AGX Orin: https://www.nvidia.com/en-gb/autonomous-machines/embedded-systems/jetson-orin/
2. NVIDIA — Jetson Thor: https://www.nvidia.com/en-gb/autonomous-machines/embedded-systems/jetson-thor/
3. NVIDIA Developer — Jetson FAQ/pricing: https://developer.nvidia.com/embedded/faq
4. NVIDIA — Jetson modules comparison: https://developer.nvidia.com/embedded/jetson-modules
5. NVIDIA Technical Blog — Jetson Thor: https://developer.nvidia.com/blog/introducing-jetson-thor-the-ultimate-platform-for-physical-ai-and-humanoid-robotics/
6. NVIDIA — Jetson Benchmarks: https://developer.nvidia.com/embedded/jetson-benchmarks
7. NVIDIA — T5000 module datasheet: current Jetson Thor documentation
8. NVIDIA — Jetson AGX Orin Thermal Design Guide: current Jetson download center
9. NVIDIA — Jetson Thor Thermal Design Guide: current Jetson download center
10. NVIDIA — Jetson AGX Orin Developer Kit documentation
11. Connect Tech — AGX Orin carrier boards: https://connecttech.com/product-category/form-factors/nvidia-jetson-agx-orin/
12. Connect Tech — Thor carrier boards: https://connecttech.com/product-category/form-factors/nvidia-jetson-thor/
13. UK RS — AGX Orin 64GB Developer Kit current listing
14. UK Scan — T5000 current listing
15. UK battery market examples: Eco-Worthy, Renogy, Ritar, Bioenno and related current listings.

Vendor prices and stock are volatile. Prices in this document are dated research observations and planning ranges, not procurement commitments.

## 32. Final decision status

```text
AGX Orin 64GB mobile       → PREFERRED CANDIDATE
Thor mobile                → CONDITIONAL CANDIDATE
Thor stationary            → STRONG CANDIDATE
Final purchase             → NOT YET APPROVED

Required next evidence:
real models + real sensors + real motors + real battery + thermal test
```
