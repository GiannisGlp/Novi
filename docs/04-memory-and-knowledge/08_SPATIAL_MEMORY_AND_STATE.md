# 08 — Spatial Memory and State

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how Novi represents locations, regions, coordinate systems, movement, spatial uncertainty and place identity.

## Core principle

```text
LOCATION = POSITION + REFERENCE FRAME + TIME + UNCERTAINTY
```

A coordinate without its reference system and observation time is incomplete.

## Spatial primitives

Support point, line, path, polygon, region, place, topology, containment, proximity, adjacency, route and movement state. Spatial representations must declare coordinate reference system, units, precision and provenance where applicable.

## Location vs place

A location is a spatial state. A place is a semantically identified entity that may occupy changing locations. `06` governs place/entity identity; `08` governs spatial state.

## Spatial uncertainty

Represent error bounds or confidence rather than false precision. GPS-like measurements, inferred locations and remembered addresses must remain distinguishable.

## Temporal coupling

Every consequential location claim is time-scoped. Movement is represented as transitions between states, not as a single timeless coordinate.

## Spatial evidence

Evidence may come from sensors, maps, user statements, device state, visual recognition, network positioning or external data. Source authority is claim-dependent and follows `03`.

## Coordinate transformations

Transformations must record source and destination reference systems and transformation metadata. Never silently mix geographic, projected, local or semantic coordinate systems.

## Spatial queries

Canonical operations include nearest, within, contains, intersects, overlaps, route, reachable, entered, exited, moved-between and as-of-location queries.

## Privacy

Location is sensitive. Store only required precision, enforce retention and access policies, and support spatial generalization when exact coordinates are unnecessary.

## Spatial conflicts

Classify stale position, sensor disagreement, coordinate mismatch, map-version mismatch, identity mismatch and genuine movement separately.

## Safety invariants

1. Coordinates require reference-frame semantics.
2. Location claims are time-dependent.
3. Preserve uncertainty and precision.
4. Never expose exact location when coarse location satisfies the task.
5. Model inference is not direct observation.
6. Spatial history remains provenance-linked.

## Integration

`06` handles place identity. `07` handles temporal state. `09` uses spatial transitions in causal models. `10` fuses spatial evidence across modalities. `14/111` govern location privacy. `109` governs distributed spatial-state convergence.