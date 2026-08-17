# 08 — Spatial Memory and State

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define how Novi represents locations, regions, coordinate systems, movement, spatial uncertainty and place identity.

## Core principle

```text
LOCATION = POSITION + REFERENCE FRAME + TIME + UNCERTAINTY
```

A coordinate without its reference system and observation time is incomplete.

## Spatial primitives

Support point, line, path, polygon, region, place, topology, containment, proximity, adjacency, route and movement state. Spatial representations must declare coordinate reference system, units, precision and provenance where applicable.

## Spatial record contract

A consequential spatial assertion should be able to represent:

```text
position / geometry
reference_frame / CRS
units
epoch / timestamp
precision
uncertainty_bounds
source_refs
provenance_ref
validity_interval
transformation_refs
privacy_class
```

Do not silently convert between geographic, projected, local or semantic coordinate systems.

## Location vs place

A location is a spatial state. A place is a semantically identified entity that may occupy changing locations. `06` governs place/entity identity; `08` governs spatial state.

## Spatial uncertainty

Represent error bounds or confidence rather than false precision. GPS-like measurements, inferred locations and remembered addresses must remain distinguishable.

## Temporal coupling

Every consequential location claim is time-scoped. Movement is represented as transitions between states, not as a single timeless coordinate.

## Spatial evidence

Evidence may come from sensors, maps, user statements, device state, visual recognition, network positioning or external data. Source authority is claim-dependent and follows `03`.

## Coordinate transformations

Transformations must record source and destination reference systems and transformation metadata. A transformation must be reproducible or identifiable where the result is consequential.

## Spatial queries

Canonical operations include nearest, within, contains, intersects, overlaps, route, reachable, entered, exited, moved-between and as-of-location queries.

Queries should specify required spatial precision and whether historical or current state is requested.

## Current localization precedence

Historical spatial memory can inform hypotheses and retrieval but must not override fresh authoritative localization when current position is required.

## Privacy

Location is sensitive. Store only required precision, enforce retention and access policies, and support spatial generalization when exact coordinates are unnecessary.

## Spatial conflicts

Classify stale position, sensor disagreement, coordinate mismatch, map-version mismatch, identity mismatch and genuine movement separately.

## Evaluation

Test spatial reasoning with coordinate-frame mismatch, uncertainty bounds, map-version drift, stale positions, indoor/outdoor transitions, entity ambiguity, route constraints and privacy-preserving generalization. Measure localization error, reference-frame correctness, temporal correctness and unauthorized precision exposure.

## Safety invariants

1. Coordinates require reference-frame semantics.
2. Location claims are time-dependent.
3. Preserve uncertainty and precision.
4. Never expose exact location when coarse location satisfies the task.
5. Model inference is not direct observation.
6. Spatial history remains provenance-linked.
7. Current authoritative localization outranks stale historical memory for current-state decisions.

## Integration

`06` handles place identity. `07` handles temporal state. `09` uses spatial transitions in causal models. `10` fuses spatial evidence across modalities. `14` governs location privacy. Distributed spatial-state convergence belongs to system architecture.