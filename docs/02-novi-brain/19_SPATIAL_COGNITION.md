# 19 — Spatial Cognition

**Status:** SUPERSEDED — legacy Brain source document  
**Canonical semantic owner:** `03-cognition/02_WORLD_MODEL.md`  
**Related authorities:** `05-hardware`, system architecture, navigation/robotics contracts, `04-memory-and-knowledge/08_SPATIAL_MEMORY_AND_STATE.md`

## Why this file was superseded

The former document combined three different responsibilities: physical localization/runtime state, semantic spatial reasoning, and historical spatial memory. Keeping them under Brain created duplicate authority.

## Canonical separation

```text
PHYSICAL SPATIAL STATE
  pose / frames / transforms / localization / sensor geometry
  → robotics + Brain/runtime authority

CURRENT SEMANTIC SPATIAL UNDERSTANDING
  places / relations / visibility / reachability / spatial beliefs
  → Cognition / World Model authority

HISTORICAL SPATIAL EXPERIENCE
  previous locations / place history / spatial memories
  → Memory & Knowledge authority

NAVIGATION
  collision-free route generation and execution
  → robotics/navigation authority
```

## Consolidated requirements

The former specification's important requirements remain architectural requirements:

- metric and topological spatial representations;
- egocentric and allocentric reasoning;
- coordinate-frame correctness;
- place recognition;
- object permanence under uncertainty;
- spatial relationships and visibility;
- affordances and reachability as non-authorizing beliefs;
- spatial prediction and change detection;
- active perception driven by information gaps;
- spatial uncertainty and conservative degradation;
- action-consequence observation;
- spatial reasoning grounded in language rather than invented coordinates;
- validation across simulation, HIL and physical testing.

Semantic requirements belong in the canonical World Model. Historical requirements belong in Memory. Runtime and hardware requirements belong in their respective domains.

## NVIDIA boundary

Isaac ROS, Isaac Sim, Nav2 and other NVIDIA/robotics technologies are implementation candidates. They do not own Novi's semantic spatial model.

## Migration rule

Do not add new semantic spatial-cognition architecture here. Extend the canonical owner instead.

## Historical preservation

The complete pre-consolidation specification remains available in Git history for provenance and recovery.
