"""Entity knowledge graph for the Mac Brain.

Extracts and maintains entity→relation→entity triples from episodic memory and
observations, forming a durable semantic knowledge graph with confidence,
provenance, entity typing, and contradiction handling.

Boundaries honored (docs/04-memory-and-knowledge/12):
  - Learning/graph evolution is memory-level operation, never schema mutation.
  - Knowledge is evidence-backed and revisable; contradictions are preserved
    rather than resolved by overwrite.
  - Knowledge feeds reasoning/recall; it is not authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

ENTITY_TYPES = {"person", "place", "building", "object", "concept"}
# Rooms / areas / outdoor zones Novi can recognise as places.
_PLACE_LABELS = {"door", "room", "kitchen", "window", "table", "hall", "office", "garage", "garden", "living room", "bedroom", "bathroom", "hallway", "yard", "street", "park", "corridor", "lobby"}
# Buildings / landmarks (docs/03-cognition/02 entity types: Place, Building).
_BUILDING_LABELS = {"house", "tower", "school", "hospital", "store", "shop", "mall", "bridge", "station", "airport", "library", "museum", "cafe", "restaurant", "bank", "factory", "church", "campus", "building"}
_PERSON_LABELS = {"alice", "bob", "vano", "charlie", "dana", "eve"}

_PREDICATES = {
    "near": "located_near",
    "in": "in",
    "on": "on",
    "has": "has",
    "is": "is",
    "moved": "moved",
    "carried": "carried",
    "watered": "tends",
    "likes": "likes",
    "owns": "owns",
    "followed": "followed",
}


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class KnowledgeTriple:
    subject: str
    predicate: str
    object: str
    confidence: float
    evidence_count: int
    status: str  # active | contradicted
    source: str = ""
    first_seen_cycle: int = 0
    last_seen_cycle: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
            "status": self.status,
            "source": self.source,
            "first_seen_cycle": self.first_seen_cycle,
            "last_seen_cycle": self.last_seen_cycle,
        }


def infer_entity_type(entity: str) -> str:
    e = entity.lower().strip()
    if e in _PERSON_LABELS:
        return "person"
    if e in _BUILDING_LABELS:
        return "building"
    if e in _PLACE_LABELS:
        return "place"
    return "object"


class EntityKnowledgeGraph:
    def __init__(self, *, on_change: Callable[[], None] | None = None) -> None:
        self._entities: dict[str, str] = {}  # entity -> type
        self._triples: dict[tuple[str, str, str], KnowledgeTriple] = {}
        self._on_change = on_change  # incremental-persistence hook (if any)

    # ---- graph construction ----
    def set_on_change(self, callback: Callable[[], None]) -> None:
        """Attach a callback invoked after every mutation, for incremental persistence."""
        self._on_change = callback

    def _notify_change(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def add(self, subject: str, predicate: str, object: str, *, confidence: float, source: str = "", cycle: int = 0) -> KnowledgeTriple:
        subject, predicate, object = subject.strip(), predicate.strip(), object.strip()
        if not subject or not predicate or not object:
            raise ValueError("subject, predicate and object are required")
        self._entities.setdefault(subject, infer_entity_type(subject))
        self._entities.setdefault(object, infer_entity_type(object))
        key = (subject, predicate, object)
        if key in self._triples:
            t = self._triples[key]
            t.evidence_count += 1
            t.confidence = 1.0 - (1.0 - t.confidence) * (1.0 - _clamp01(confidence))
            t.last_seen_cycle = max(t.last_seen_cycle, cycle)
        else:
            t = self._triples[key] = KnowledgeTriple(subject, predicate, object, _clamp01(confidence), 1, "active", source, cycle, cycle)
        self._reconcile_conflicts(subject, predicate)
        self._notify_change()
        return t

    def _reconcile_conflicts(self, subject: str, predicate: str) -> None:
        """Among (subject,predicate,*) triples, the highest-confidence object stays
        active; all others are marked contradicted (evidence is preserved)."""
        group = [t for (s, p, o), t in self._triples.items() if s == subject and p == predicate]
        if not group:
            return
        lead = max(group, key=lambda t: (t.confidence, t.evidence_count))
        for t in group:
            t.status = "active" if t is lead else "contradicted"

    # ---- extraction from episodic text ----
    def extract_from_text(self, text: str, entity_refs: tuple[str, ...]) -> list[tuple[str, str, str]]:
        if len(entity_refs) < 2:
            return []
        lowered = text.lower()
        predicate = next((pred for word, pred in _PREDICATES.items() if word in lowered), "related_to")
        subject = entity_refs[0]
        return [(subject, predicate, obj) for obj in entity_refs[1:]]

    # ---- queries ----
    def triples(self, *, subject: str | None = None, predicate: str | None = None, object: str | None = None) -> tuple[KnowledgeTriple, ...]:
        out = []
        for (s, p, o), t in self._triples.items():
            if subject is not None and s != subject:
                continue
            if predicate is not None and p != predicate:
                continue
            if object is not None and o != object:
                continue
            out.append(t)
        out.sort(key=lambda t: (-t.confidence, -t.evidence_count))
        return tuple(out)

    def leading(self, subject: str, predicate: str) -> KnowledgeTriple | None:
        group = self.triples(subject=subject, predicate=predicate)
        return group[0] if group else None

    def has_conflict(self, subject: str, predicate: str) -> bool:
        return len(self.triples(subject=subject, predicate=predicate)) > 1

    def contradicted(self) -> tuple[KnowledgeTriple, ...]:
        return tuple(t for t in self._triples.values() if t.status == "contradicted")

    def context(self, entity: str, *, limit: int = 10) -> tuple[KnowledgeTriple, ...]:
        out = [t for t in self._triples.values() if entity in (t.subject, t.object)]
        out.sort(key=lambda t: (-t.confidence, -t.evidence_count))
        return tuple(out[:limit])

    # ---- graph analytics (gap-audit Phase D1) ----

    def query(self, entity: str, *, predicate: str | None = None, hops: int = 1) -> list[dict[str, Any]]:
        """BFS multi-hop neighbourhood query from ``entity``.

        Follows triple edges outward (subject→object) and inward (object→
        subject) up to ``hops``; ``predicate`` filters edges when given.
        Returns deduplicated rows with the hop distance. Deterministic order:
        by hop, then subject/predicate/object.
        """
        entity = str(entity).strip()
        if not entity or hops < 1:
            return []
        out_edges: dict[str, list[tuple[str, str]]] = {}   # node -> [(predicate, node)]
        in_edges: dict[str, list[tuple[str, str]]] = {}
        for (s, p, o) in self._triples:
            out_edges.setdefault(s, []).append((p, o))
            in_edges.setdefault(o, []).append((p, s))
        rows: dict[tuple[str, str, str, int], dict[str, Any]] = {}
        seen_nodes = {entity}
        frontier = [entity]
        for depth in range(1, hops + 1):
            nxt: list[str] = []
            for node in frontier:
                for p, other in out_edges.get(node, []):
                    if predicate is not None and p != predicate:
                        continue
                    key = (node, p, other, depth)
                    if key not in rows:
                        rows[key] = {"subject": node, "predicate": p, "object": other, "hops": depth}
                    if other not in seen_nodes:
                        seen_nodes.add(other)
                        nxt.append(other)
                for p, other in in_edges.get(node, []):
                    if predicate is not None and p != predicate:
                        continue
                    key = (other, p, node, depth)
                    if key not in rows:
                        rows[key] = {"subject": other, "predicate": p, "object": node, "hops": depth}
                    if other not in seen_nodes:
                        seen_nodes.add(other)
                        nxt.append(other)
            frontier = nxt
        return sorted(rows.values(), key=lambda r: (r["hops"], r["subject"], r["predicate"], r["object"]))

    def pagerank(self) -> dict[str, float]:
        """Entity importance via PageRank (networkx when available).

        Fallback without networkx: normalized confidence-weighted degree — a
        principled, cheap proxy that keeps the API honest offline. All scores
        are in [0, 1].
        """
        if not self._triples:
            return {}
        weights: dict[str, float] = {}
        for (s, _p, o), t in self._triples.items():
            w = max(0.0, min(1.0, float(t.confidence)))
            weights[s] = weights.get(s, 0.0) + w
            weights[o] = weights.get(o, 0.0) + w
        try:
            import networkx as nx
        except Exception:  # noqa: BLE001 - optional extra; degree fallback below
            total = sum(weights.values()) or 1.0
            return {k: round(v / total, 6) for k, v in sorted(weights.items())}
        # Undirected view: importance = how strongly an entity participates
        # in relations at all, regardless of argument order.
        g = nx.Graph()
        for (s, p, o), t in sorted(self._triples.items()):
            w = max(0.0, min(1.0, float(t.confidence)))
            if g.has_edge(s, o):
                g[s][o]["weight"] += w
                g[s][o]["predicates"].add(p)
            else:
                g.add_edge(s, o, weight=w, predicates={p})
        ranks = nx.pagerank(g, weight="weight")
        return {k: round(float(v), 6) for k, v in sorted(ranks.items())}

    def top_entities(self, *, limit: int = 5) -> list[tuple[str, float]]:
        ranks = self.pagerank()
        return sorted(ranks.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]

    def entity_types(self) -> dict[str, str]:
        return dict(self._entities)

    def counts(self) -> dict[str, int]:
        return {"entities": len(self._entities), "triples": len(self._triples), "contradicted": len(self.contradicted())}

    # ---- persistence ----
    def snapshot(self) -> dict[str, Any]:
        return {
            "entities": dict(self._entities),
            "triples": [t.snapshot() for t in self._triples.values()],
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any], *, on_change: Callable[[], None] | None = None) -> "EntityKnowledgeGraph":
        graph = cls(on_change=on_change)
        graph._entities = {k: v for k, v in data.get("entities", {}).items()}
        for row in data.get("triples", []):
            t = KnowledgeTriple(
                subject=row["subject"],
                predicate=row["predicate"],
                object=row["object"],
                confidence=row["confidence"],
                evidence_count=row["evidence_count"],
                status=row["status"],
                source=row.get("source", ""),
                first_seen_cycle=row.get("first_seen_cycle", 0),
                last_seen_cycle=row.get("last_seen_cycle", 0),
            )
            graph._triples[(t.subject, t.predicate, t.object)] = t
        return graph
