# 10 — Autonomy Event Bus

## Status

**DESIGN**

## Purpose

The event bus decouples perception, cognition, memory, autonomy, tools, diagnostics, and UI while allowing Novi to react continuously.

## Requirements

The bus must support:

- typed events;
- timestamps;
- correlation IDs;
- causation IDs;
- priority;
- delivery semantics;
- replay;
- deduplication;
- backpressure;
- health monitoring;
- access control.

## Event Envelope

```json
{
  "event_id": "uuid",
  "type": "person.entered_room",
  "version": 1,
  "occurred_at": "timestamp",
  "published_at": "timestamp",
  "source": "vision",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "priority": "normal",
  "privacy_class": "private",
  "payload": {}
}
```

## Delivery

Critical safety events require stronger delivery guarantees than ephemeral UI animations. Each event type defines its required delivery semantics.

## Ordering

Ordering is defined within a relevant partition/correlation domain, not globally. Consumers must tolerate delayed and duplicate events.

## Persistence

Events that are needed for audit, replay, world-state reconstruction, or learning are persisted. High-rate sensor data can use separate streaming/storage paths.

## Replay

A recorded event stream can drive a simulated autonomy runtime. Replay must support deterministic clocks and controlled model stubs for regression tests.

## Backpressure

Consumers must not allow a burst of low-value events to starve safety or interactive events. Queues require bounded memory and priority-aware handling.

## NVIDIA Integration

On Jetson, high-bandwidth sensor/video paths may use NVIDIA-accelerated components such as Isaac ROS or DeepStream where they materially improve throughput/latency. The event-bus contract remains independent of the transport implementation.

## Acceptance Criteria

- duplicate-safe consumers;
- priority-aware delivery;
- replayable autonomy events;
- bounded queues;
- observable delivery failures;
- no untrusted event can bypass capability authorization.
