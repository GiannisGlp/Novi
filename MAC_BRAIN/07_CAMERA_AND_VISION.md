# Mac Brain Camera and Vision

## Objective

Turn camera frames into validated perception evidence suitable for world-state updates and multimodal reasoning.

## Pipeline

```text
Camera
 -> capture/timestamp
 -> preprocessing
 -> detection/depth/VLM providers
 -> normalized evidence
 -> validation
 -> world state
```

## Initial capabilities

- object detection;
- person detection;
- scene understanding;
- change/event detection;
- depth where available;
- confidence/validity tracking.

## Acceptance direction

The camera pipeline must maintain timestamps, provenance and uncertainty and must reject invalid or stale observations before they become trusted world state.
