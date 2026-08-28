# 10 — Runtime, Deployment and Hardware

## Objective

Keep Novi's autonomy architecture portable across the current Mac development environment and the future NVIDIA/robot runtime.

## Architecture rule

```text
Novi cognition/autonomy contracts
            ↓
Hardware-neutral providers
            ↓
┌───────────────┬──────────────────┐
│ Mac/MPS       │ NVIDIA/ROS2       │
│ development   │ robot deployment  │
└───────────────┴──────────────────┘
```

## Step-by-step

### Step 1 — Define provider interfaces

Create boundaries for:

- `CameraProvider`;
- `DepthProvider`;
- `PoseProvider`;
- `MapProvider`;
- `NavigationProvider`;
- `ManipulationProvider`;
- `Motor/ActuatorProvider`;
- `AudioProvider`;
- `PowerProvider`;
- `ComputeHealthProvider`.

### Step 2 — Keep core dependencies light

The brain must not import ROS2, CUDA, TensorRT or Isaac-specific packages directly. Adapters own those dependencies.

### Step 3 — Mac development backend

Continue validating perception and cognition on Apple MPS. Heavy NVIDIA-only components remain optional and must fail gracefully when unavailable.

### Step 4 — ROS2 integration boundary

When the robot hardware is defined, connect sensors, transforms, navigation and control through ROS2/standard robotics interfaces. Agentic reasoning should sit above these tested robot primitives rather than replacing them. Research on embodied agent systems similarly emphasizes adding LLM/VLM reasoning on top of established robot middleware rather than discarding the underlying stack.

### Step 5 — NVIDIA simulation environment

Use Isaac Sim for physically grounded simulation, sensor simulation, ROS2 connectivity, synthetic data and SIL/HIL validation. NVIDIA documents URDF/MJCF import, physics sensors, ROS2 integration, Replicator synthetic data and SIL/HIL workflows. citeturn0search0turn0search4

### Step 6 — NVIDIA robot deployment

Once the physical robot is specified, select Jetson/GPU hardware from measured requirements. Do not choose hardware solely from model size. Benchmark:

- perception FPS;
- VLM query latency;
- planning latency;
- memory usage;
- thermal behavior;
- power consumption;
- end-to-end control-loop latency.

### Step 7 — Containerize

Provide separate runtime profiles for:

- core-only development;
- Mac perception;
- NVIDIA GPU perception;
- simulation;
- physical robot.

### Step 8 — Add runtime degradation

If GPU, network, VLM, depth or a secondary sensor disappears, Novi should reduce capability/authority rather than pretending the system is healthy.

### Step 9 — Hardware-in-loop

Connect the real compute and sensor/control interfaces to simulation before permitting physical autonomous movement. Verify timing, transforms, actuator limits and emergency stop behavior.

### Step 10 — Physical deployment ladder

1. read-only sensors;
2. perception only;
3. virtual actions;
4. motors disabled;
5. supervised low-speed motion;
6. bounded autonomous tasks;
7. longer supervised runs;
8. only then broader autonomy.

## Acceptance gate

`A-RUNTIME-01`: The same autonomy contracts must pass on the simulation backend and the selected robot backend without changing cognition/planning semantics.
