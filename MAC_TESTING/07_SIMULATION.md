# Mac Simulation Testing

## Objective

Create deterministic, hardware-independent scenarios that exercise Brain and future autonomy logic.

## Initial approach

Start with lightweight replay/synthetic scenarios rather than requiring a full 3D simulator for every test.

Examples:

- static obstacle;
- moving obstacle;
- person entering path;
- changing scene;
- stale sensor frame;
- missing depth;
- reasoning timeout;
- conflicting evidence.

## Future expansion

Isaac Sim or another simulator can become a higher-fidelity validation environment. Scenario definitions should remain portable so the same logical tests can be reused.
