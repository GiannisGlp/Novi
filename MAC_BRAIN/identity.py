"""Person identity recognition for the Mac Brain.

Implements the Cognition person model (docs/03-cognition 03 example, docs/06-soul/04,
docs/02-autonomy/03): combine camera detections, face observations, and naming (speech)
into a per-person **identity belief** that is explicitly separated into
**detected / probable / verified** tiers, each with confidence and provenance.

Boundaries honored:
  - Recognition confidence is never authorization; identity never overrides safety,
    privacy, or consent.
  - Uncertain identity is preserved as uncertainty (never asserted as a fact).
  - A detected/probable/verified tier must be revisable as new evidence arrives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VERIFIED_CONFIDENCE = 0.8
PROBABLE_CONFIDENCE = 0.55
CROSS_MODAL_COUNT = 2


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class IdentityBelief:
    person: str
    name: str | None
    confidence: float
    tier: str  # detected | probable | verified
    evidence_count: int
    modalities: tuple[str, ...]
    last_seen_cycle: int

    @property
    def known(self) -> bool:
        return self.name is not None and self.tier in ("probable", "verified")

    def snapshot(self) -> dict[str, Any]:
        return {
            "person": self.person,
            "name": self.name,
            "confidence": round(self.confidence, 3),
            "tier": self.tier,
            "evidence_count": self.evidence_count,
            "modalities": list(self.modalities),
            "last_seen_cycle": self.last_seen_cycle,
        }


class PersonIdentity:
    """Accumulates per-person identity evidence and yields identity beliefs."""

    def __init__(self) -> None:
        self._presence: dict[str, int] = {}  # person -> last_seen_cycle
        # person -> name -> {confidences, modalities, cycles}
        self._bindings: dict[str, dict[str, dict[str, Any]]] = {}

    def observe(self, person: str, *, confidence: float, modality: str, cycle: int, name: str | None = None) -> None:
        person = person or "unknown"
        self._presence[person] = max(self._presence.get(person, 0), cycle)
        if name is None or not name.strip():
            return
        binding = self._bindings.setdefault(person, {}).setdefault(name.strip(), {"confidences": [], "modalities": set(), "cycle": cycle})
        binding["confidences"].append(_clamp01(confidence))
        binding["modalities"].add(modality)
        binding["cycle"] = max(int(binding["cycle"]), cycle)

    def _combined(self, confidences: list[float]) -> float:
        if not confidences:
            return 0.0
        product = 1.0
        for c in confidences:
            product *= 1.0 - c
        return 1.0 - product

    def identity_for(self, person: str) -> IdentityBelief | None:
        person = person or "unknown"
        last = self._presence.get(person)
        if last is None:
            return None
        bindings = self._bindings.get(person)
        if not bindings:
            return IdentityBelief(person, None, 0.0, "detected", 0, (), last)
        best = None
        best_key = None
        best_score = (-1.0, -1, -1)
        for name, binding in bindings.items():
            conf = self._combined(binding["confidences"])
            score = (conf, len(binding["confidences"]), len(binding["modalities"]))
            if score > best_score:
                best_score = score
                best = (name, conf, binding)
        name, conf, binding = best
        if len(binding["confidences"]) >= CROSS_MODAL_COUNT and len(binding["modalities"]) >= CROSS_MODAL_COUNT and conf >= VERIFIED_CONFIDENCE:
            tier = "verified"
        elif conf >= PROBABLE_CONFIDENCE:
            tier = "probable"
        else:
            tier = "detected"
        return IdentityBelief(person, name, round(conf, 3), tier, len(binding["confidences"]), tuple(sorted(binding["modalities"])), last)

    def is_known(self, person: str) -> bool:
        belief = self.identity_for(person)
        return bool(belief and belief.known)

    def tier(self, person: str) -> str:
        belief = self.identity_for(person)
        return belief.tier if belief else "detected"

    def snapshot(self) -> dict[str, Any]:
        return {
            "presence": dict(self._presence),
            "bindings": {
                person: {
                    name: {"confidences": b["confidences"], "modalities": sorted(b["modalities"]), "cycle": b["cycle"]}
                    for name, b in names.items()
                }
                for person, names in self._bindings.items()
            },
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "PersonIdentity":
        model = cls()
        model._presence = {k: int(v) for k, v in data.get("presence", {}).items()}
        for person, names in data.get("bindings", {}).items():
            for name, b in names.items():
                model._bindings.setdefault(person, {})[name] = {
                    "confidences": list(b.get("confidences", [])),
                    "modalities": set(b.get("modalities", [])),
                    "cycle": int(b.get("cycle", 0)),
                }
        return model
