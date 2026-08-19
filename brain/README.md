# Novi Brain — Stage 0

This package is the first executable Brain runtime baseline.

Stage 0 deliberately uses a modular-monolith architecture with deterministic lifecycle, scheduling, typed runtime events and a mock body. It does not require neural models, ROS 2, NVIDIA hardware, or physical robot hardware.

## Run

```bash
python3 -m brain.main --cycles 1
```

## Test

```bash
python3 -m unittest discover -s brain/tests -v
```

## Scope

- supervisor lifecycle;
- deterministic scheduler;
- runtime event envelope;
- health and structured errors;
- synthetic observation source;
- mock safety gateway;
- mock body;
- one deterministic closed runtime cycle.

The implementation consumes the existing contract architecture and does not create competing semantic authorities for Soul, Cognition, Memory, Autonomy or Safety.