"""Spatial model for the Mac Brain (roadmap item 11; P4 spatial gap).

Implements the spatial requirements of
docs/03-cognition/02_WORLD_MODEL.md (Spatial Model) and the coordinate/frame
contract of docs/03-cognition/22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md §20:

  - named coordinate frames with explicit parent transforms and units;
  - rooms / floors / zones / doors with metric bounds and topological
    connectivity;
  - occupancy state per region ("free"/"occupied"/"unknown");
  - the metric-vs-semantic link: a pose is always expressed in a named frame
    (explicit units) and maps to semantic regions via bounds tests;
  - visibility and reachability queries (topology-aware).

The typed contract object `cognition.contracts.common.SpatialReference` remains
the exchange format; this module provides the runtime spatial model that fills
it, and `SpatialMap.to_spatial_state()` feeds the typed `WorldState.spatial_state`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from novi.cognition.contracts.common import SpatialReference

METRE = "m"
DEG = "deg"


def convert_distance_m(value_m: float, to_unit: str) -> float:
    """Convert a distance in metres to ``to_unit`` using pint (lazy import).

    Units are attached at input (metres) and stripped only at output, per the
    uncertainty-and-units skill. Raises ``ValueError`` for a non-length unit.
    Falls back to identity (returns ``value_m``) if pint is unavailable.
    """
    try:
        from pint import UnitRegistry
    except ImportError:  # pragma: no cover - pint optional
        return value_m
    ureg = UnitRegistry()
    q = value_m * ureg.metre
    try:
        return q.to(to_unit).magnitude
    except Exception as exc:  # pint raises DimensionalityError / UndefinedUnitError
        raise ValueError(f"cannot convert metres to {to_unit!r}: {exc}") from exc


# Convenience literals for bounding boxes that lint cleanly.
Bounds2D = tuple[float, float]
RegionBounds = tuple[Bounds2D, Bounds2D]


def _bounds_covered(inner: Region, outer: Region) -> bool:
    """True when inner's bounds are fully inside outer's bounds (same frame)."""
    if inner.frame != outer.frame:
        return False
    return (
        outer.bounds_x[0] <= inner.bounds_x[0]
        and inner.bounds_x[1] <= outer.bounds_x[1]
        and outer.bounds_y[0] <= inner.bounds_y[0]
        and inner.bounds_y[1] <= outer.bounds_y[1]
    )


def _contains(inner: Region, outer: Region) -> bool:
    return _bounds_covered(inner, outer)


def _contains_bounds(ra: Region, rb: Region) -> bool:
    """Either region's bounds are fully inside the other's (same frame)."""
    if ra.frame != rb.frame:
        return False
    return _bounds_covered(ra, rb) or _bounds_covered(rb, ra)


def _same_bounds(ra: Region, rb: Region) -> bool:
    return ra.frame == rb.frame and ra.bounds_x == rb.bounds_x and ra.bounds_y == rb.bounds_y


@dataclass(frozen=True, order=True)
class Pose2D:
    """A 2-D pose in a named frame (x_m, y_m, heading_rad).

    Units are attached at input (the ``_m`` / ``_rad`` suffixes) and stripped
    only at output. Standard uncertainties (``*_unc_*``) are carried alongside
    each coordinate so downstream distance/heading calculations can propagate
    them (uncertainty-and-units skill: GUM linearization).
    """

    x_m: float = 0.0
    y_m: float = 0.0
    heading_rad: float = 0.0
    x_unc_m: float = 0.0
    y_unc_m: float = 0.0
    heading_unc_rad: float = 0.0

    def distance_to(self, other: "Pose2D") -> tuple[float, float]:
        """Euclidean distance to ``other`` and its propagated standard uncertainty.

        Returns ``(distance_m, distance_uncertainty_m)``. The uncertainty is
        propagated by GUM linearization (sensitivity coefficients times the
        input standard uncertainties, combined in quadrature). A zero distance
        with non-zero input uncertainty yields a conservative ``0.0``
        uncertainty (the linearization is singular at the origin).
        """
        dx = other.x_m - self.x_m
        dy = other.y_m - self.y_m
        dist = (dx * dx + dy * dy) ** 0.5
        if dist == 0.0:
            return 0.0, 0.0
        # Sensitivity coefficients: c_x = dx/d, c_y = dy/d.
        cx = dx / dist
        cy = dy / dist
        u = (
            (cx * self.x_unc_m) ** 2 + (cx * other.x_unc_m) ** 2 + (cy * self.y_unc_m) ** 2 + (cy * other.y_unc_m) ** 2
        ) ** 0.5
        return dist, u

    def snapshot(self) -> dict[str, float]:
        return {
            "x": self.x_m,
            "y": self.y_m,
            "heading_rad": self.heading_rad,
            "x_unc_m": self.x_unc_m,
            "y_unc_m": self.y_unc_m,
            "heading_unc_rad": self.heading_unc_rad,
        }


@dataclass(frozen=True)
class SpatialFrame:
    """A named coordinate frame with its parent and static transform."""

    name: str
    parent: str | None = None
    origin: Pose2D = Pose2D()
    units: str = "m"
    description: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "parent": self.parent,
            "origin": self.origin.snapshot(),
            "units": self.units,
            "description": self.description,
        }


@dataclass(frozen=True)
class Region:
    """A metric region (room/zone/door) in a frame with a semantic tag."""

    region_id: str
    frame: str
    kind: str  # "room" | "floor" | "zone" | "door"
    bounds_x: Bounds2D
    bounds_y: Bounds2D

    def contains(self, x: float, y: float) -> bool:
        x0, x1 = self.bounds_x
        y0, y1 = self.bounds_y
        return x0 <= x <= x1 and y0 <= y <= y1


@dataclass(frozen=True)
class DoorLink:
    """A door joins two regions (topological connectivity)."""

    door_id: str
    connects: tuple[str, str]


class SpatialMap:
    """Runtime spatial model: frames, regions, occupancy, metric<->semantic.

    Metric localization and semantic location are separate but linked: a pose
    is always expressed in a named frame (explicit units), and region bounds
    provide the metric-vs-semantic mapping.
    """

    def __init__(self) -> None:
        self._frames: dict[str, SpatialFrame] = {}
        self._regions: dict[str, Region] = {}
        self._doors: set[DoorLink] = set()
        self._occupancy: dict[str, str] = {}  # region_id -> free|occupied|unknown
        self._entity_poses: dict[str, SpatialReference] = {}
        self._version: int = 0

    def register_frame(self, frame: SpatialFrame) -> None:
        self._frames[frame.name] = frame
        self._version += 1

    def register_region(self, region: Region) -> None:
        self._regions[region.region_id] = region
        self._occupancy.setdefault(region.region_id, "unknown")
        self._version += 1

    def register_door(self, door: DoorLink) -> None:
        self._doors.add(door)
        self._version += 1

    def set_occupancy(self, region_id: str, value: str) -> None:
        if value not in ("free", "occupied", "unknown"):
            raise ValueError(f"bad occupancy: {value!r}")
        if region_id not in self._regions:
            raise KeyError(f"unknown region: {region_id}")
        self._occupancy[region_id] = value
        self._version += 1

    def occupancy(self, region_id: str) -> str:
        return self._occupancy.get(region_id, "unknown")

    # ---- entities ----

    def place(self, entity_id: str, ref: SpatialReference) -> None:
        """Attach a spatial reference (frame/pose/semantic_location/occupancy)."""
        if ref.frame_id not in self._frames:
            raise KeyError(f"unknown frame: {ref.frame_id}")
        self._entity_poses[entity_id] = ref
        self._version += 1

    def pose_of(self, entity_id: str) -> SpatialReference | None:
        return self._entity_poses.get(entity_id)

    def region_of(self, entity_id: str) -> str | None:
        ref = self._entity_poses.get(entity_id)
        if ref is None:
            return None
        x = ref.pose.get("x")
        y = ref.pose.get("y")
        if x is None or y is None:
            # Fall back to declared semantic location.
            for loc in ref.semantic_location:
                if loc in self._regions:
                    return loc
            return None
        for region in self._regions.values():
            if region.frame == ref.frame_id and region.contains(float(x), float(y)):
                return region.region_id
        return None

    def semantic_location_of(self, entity_id: str) -> list[str]:
        """Metric pose -> semantic region tags, merged with declared tags."""
        ref = self._entity_poses.get(entity_id)
        tags = list(ref.semantic_location) if ref else []
        region_id = self.region_of(entity_id)
        if region_id and region_id not in tags:
            tags.append(region_id)
        return tags

    def visible_entities(self, at_region: str) -> list[str]:
        """Entities whose region (metric) or declared location matches."""
        out = []
        for entity_id, ref in self._entity_poses.items():
            if at_region in ref.semantic_location or self.region_of(entity_id) == at_region:
                out.append(entity_id)
        return out

    def reachable_regions(self, from_region: str) -> set[str]:
        """Topological connectivity via doors + containment (BFS).

        Doors link rooms; a zone contained inside another region is treated as
        connected to its container (same-space overlap).
        """
        adj: dict[str, set[str]] = {r: set() for r in self._regions}
        for door in self._doors:
            a, b = door.connects
            if a in adj and b in adj:
                adj[a].add(b)
                adj[b].add(a)
        # Containment: a region whose bounds lie inside another's is reachable
        # through it (same physical space, no door required).
        items = list(self._regions.values())
        for i, ra in enumerate(items):
            for rb in items[i + 1 :]:
                if _contains_bounds(ra, rb):
                    adj[ra.region_id].add(rb.region_id)
                    adj[rb.region_id].add(ra.region_id)
        if from_region not in adj:
            return set()
        seen = {from_region}
        frontier = [from_region]
        while frontier:
            cur = frontier.pop()
            for nxt in adj.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
        return seen

    def visibility_between(self, a: str, b: str) -> bool:
        """Same region, directly door-connected, or one contains the other."""
        if a == b:
            return True
        if any((door.connects == (a, b)) or (door.connects == (b, a)) for door in self._doors):
            return True
        ra = self._regions.get(a)
        rb = self._regions.get(b)
        return bool(
            ra is not None and rb is not None and (_same_bounds(ra, rb) or _contains(ra, rb) or _contains(rb, ra))
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "version": self._version,
            "frames": [f.snapshot() for f in self._frames.values()],
            "regions": [
                {
                    "region_id": r.region_id,
                    "frame": r.frame,
                    "kind": r.kind,
                    "bounds_x": list(r.bounds_x),
                    "bounds_y": list(r.bounds_y),
                    "occupancy": self._occupancy.get(r.region_id, "unknown"),
                }
                for r in self._regions.values()
            ],
            "doors": [{"door_id": d.door_id, "connects": list(d.connects)} for d in self._doors],
            "entity_poses": {eid: ref.model_dump() for eid, ref in self._entity_poses.items()},
        }

    def to_spatial_state(self) -> dict[str, object]:
        """Fill the typed WorldState.spatial_state dictionary (cognition)."""
        return {
            "frames": [f.snapshot() for f in self._frames.values()],
            "regions": [
                {
                    "region_id": r.region_id,
                    "frame": r.frame,
                    "kind": r.kind,
                    "bounds_x": list(r.bounds_x),
                    "bounds_y": list(r.bounds_y),
                }
                for r in self._regions.values()
            ],
            "occupancy": dict(self._occupancy),
            "doors": [list(d.connects) for d in self._doors],
            "entity_poses": {eid: ref.model_dump() for eid, ref in self._entity_poses.items()},
        }


def default_home_map() -> SpatialMap:
    """A small deterministic example: kitchen/living/door, metric bounds."""
    m = SpatialMap()
    m.register_frame(SpatialFrame(name="map", units="m", description="global 2-D map"))
    m.register_frame(SpatialFrame(name="base", parent="map", units="m", description="robot base"))
    m.register_region(Region("kitchen", "map", "room", (0.0, 4.0), (0.0, 4.0)))
    m.register_region(Region("living_room", "map", "room", (4.0, 8.0), (0.0, 4.0)))
    m.register_region(Region("table_zone", "map", "zone", (1.0, 3.0), (1.0, 3.0)))
    m.register_region(Region("door_kl", "map", "door", (4.0, 4.0), (1.0, 3.0)))
    m.register_door(DoorLink("door_kl", ("kitchen", "living_room")))
    m.set_occupancy("kitchen", "free")
    m.set_occupancy("living_room", "free")
    return m
