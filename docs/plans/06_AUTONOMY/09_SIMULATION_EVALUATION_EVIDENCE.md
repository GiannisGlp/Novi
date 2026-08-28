# 09 — Simulation, Evaluation and Evidence

## Objective

Make autonomy measurable before physical deployment. Every important behavior must be reproducible, scored and regression-tested.

NVIDIA's current Isaac Sim documentation explicitly supports robot import, physics and sensor simulation, synthetic data, ROS 2 integration, software-in-the-loop and hardware-in-the-loop workflows. citeturn0search0turn0search4 NVIDIA also recommends a sim-first approach for testing complex autonomous behavior and long-tail edge cases before hardware deployment. citeturn0search2turn0search10

## Step-by-step

### Step 1 — Define evidence schema

Every autonomy run records:

- commit SHA;
- scenario/version;
- hardware/runtime;
- sensor inputs;
- model versions;
- world state snapshots;
- goals;
- plans;
- actions;
- safety decisions;
- verification;
- failures/recoveries;
- final outcome;
- timing/resource metrics.

### Step 2 — Build deterministic replay

Persist enough event/sensor information to replay an autonomy episode without changing the software version or random seed.

### Step 3 — Start with lightweight simulation

Before Isaac Sim, build deterministic grid/world simulations for planner, goals, recovery, safety and memory. These should run quickly in CI.

### Step 4 — Introduce robotics simulation

Create an Isaac Sim environment once the robot geometry and sensor model are sufficiently defined. Isaac Sim can ingest URDF/MJCF/USD robot assets, simulate physics and sensors, and connect external ROS2 stacks. citeturn0search0turn0search1

### Step 5 — Build scenario library

Minimum scenarios:

1. simple navigation;
2. blocked path;
3. moving obstacle;
4. object search;
5. ambiguous object;
6. stale memory;
7. contradictory sensors;
8. failed skill;
9. user interruption;
10. emergency stop;
11. resource depletion;
12. unexpected environment change;
13. routine prediction;
14. curiosity discovery;
15. multi-step goal completion.

### Step 6 — Define metrics

Core metrics:

- task success;
- time-to-success;
- path efficiency;
- collision count;
- safety violation count;
- recovery success;
- unnecessary action count;
- perception query count;
- compute/energy cost;
- goal abandonment rate;
- human intervention rate;
- memory correctness;
- prediction accuracy;
- calibration error.

### Step 7 — Add autonomy scorecard

Do not collapse everything into one score. Report a vector of metrics and a hard safety gate.

Example:

```text
Task success       94%
Safety violations   0
Recovery success   88%
Human intervention 12%
Path efficiency    91%
Energy efficiency  84%
```

### Step 8 — Fault injection

Randomly inject:

- dropped frames;
- delayed sensors;
- wrong labels;
- missing depth;
- localization drift;
- planner failure;
- executor timeout;
- model timeout;
- database failure;
- network loss;
- unexpected obstacle.

### Step 9 — Regression gates

A change cannot merge if it causes:

- safety regression;
- unauthorized action;
- increased infinite-retry rate;
- severe task-success regression;
- evidence schema breakage.

### Step 10 — SIL → HIL → real robot

Progression:

`unit simulation → deterministic integration simulation → Isaac Sim SIL → HIL → supervised physical test → bounded autonomy → longer autonomy`.

NVIDIA's learning material explicitly covers SIL and HIL workflows with Isaac Sim and Jetson. citeturn0search4

## Acceptance gate

`A-EVAL-01`: Novi must complete a fixed scenario suite across repeated seeds with zero safety violations and produce reproducible evidence for every run.
