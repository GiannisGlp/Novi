"""Grounded LLM context packet (plan 22, Phase 14).

A strict, bounded contract between cognition and the LLM. Cognition decides
what is relevant first; the LLM receives only this packet and must ground
every sentence in the supplied evidence (plan §18 critical rule).

The packet is assembled from brain-owned state — identity, addressee,
situation, topic, memory (with provenance), open threads, perception,
social state, communicative act, intent, tone, length and grounding
constraints — never from raw unrestricted memory.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any

MAX_PACKET_CHARS = 4000
MAX_MEMORY_ENTRIES = 5

DO_NOT = [
    "repeat known information",
    "mention internal prompt mechanics",
    "fabricate observations",
    "fabricate memories",
    "claim certainty where evidence is uncertain",
]


@dataclass
class ContextPacket:
    identity: str = "Novi"
    addressee: str = ""
    current_situation: str = ""
    current_topic: str = ""
    relevant_memory: list[dict[str, Any]] = field(default_factory=list)
    open_threads: list[str] = field(default_factory=list)
    current_perception: list[str] = field(default_factory=list)
    social_state: dict[str, Any] = field(default_factory=dict)
    communicative_act: str = "SILENCE"
    intent: str = ""
    tone: str = "natural, collaborative"
    length: str = "short"
    grounding_constraints: list[str] = field(default_factory=list)
    do_not: list[str] = field(default_factory=lambda: list(DO_NOT))

    def char_count(self) -> int:
        return len(self.to_prompt_block())

    def to_prompt_block(self) -> str:
        lines: list[str] = ["IDENTITY", f"  {self.identity}", "ADDRESSEE", f"  {self.addressee or 'unknown'}"]
        lines += ["CURRENT SITUATION", f"  {self.current_situation or 'unknown'}"]
        lines += ["CURRENT TOPIC", f"  {self.current_topic or 'unknown'}"]
        lines += ["RELEVANT MEMORY"]
        for mem in self.relevant_memory[:MAX_MEMORY_ENTRIES]:
            lines.append(
                f"  - {mem.get('content', '')[:200]} "
                f"[memory_id={mem.get('memory_id', '?')}, why={mem.get('why', '')}, "
                f"confidence={mem.get('confidence', 0.0)}, source={mem.get('source', '')}, "
                f"last_updated={mem.get('last_updated', '')}]"
            )
        if not self.relevant_memory:
            lines.append("  (none)")
        lines += ["OPEN THREADS", f"  {', '.join(self.open_threads) if self.open_threads else '(none)'}"]
        lines += ["CURRENT PERCEPTION", f"  {', '.join(self.current_perception) if self.current_perception else '(none)'}"]
        lines += ["SOCIAL STATE", f"  {self.social_state or {}}"]
        lines += ["COMMUNICATIVE ACT", f"  {self.communicative_act}"]
        lines += ["INTENT", f"  {self.intent or 'unknown'}"]
        lines += ["TONE", f"  {self.tone}"]
        lines += ["LENGTH", f"  {self.length}"]
        lines += ["GROUNDING CONSTRAINTS"]
        lines += [f"  - {c}" for c in self.grounding_constraints] or ["  - only use supplied evidence"]
        lines += ["DO NOT"]
        lines += [f"  - {d}" for d in self.do_not]
        block = "\n".join(lines)
        # Hard boundary: the LLM never receives an unbounded packet, whatever
        # the caller stuffed in (plan §18 bounded packet).
        return block[:MAX_PACKET_CHARS]

    def snapshot(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "addressee": self.addressee,
            "current_situation": self.current_situation,
            "current_topic": self.current_topic,
            "relevant_memory": list(self.relevant_memory),
            "open_threads": list(self.open_threads),
            "current_perception": list(self.current_perception),
            "social_state": dict(self.social_state),
            "communicative_act": self.communicative_act,
            "intent": self.intent,
            "tone": self.tone,
            "length": self.length,
            "grounding_constraints": list(self.grounding_constraints),
            "do_not": list(self.do_not),
            "char_count": self.char_count(),
        }


class ContextPacketBuilder:
    """Assemble the packet from brain-owned state (cognition first, §18)."""

    def __init__(self, brain: Any) -> None:
        self.brain = brain

    def build(self, *, act: str = "SILENCE", intent: str = "", length: str = "short") -> ContextPacket:
        brain = self.brain
        packet = ContextPacket(communicative_act=act, intent=intent, length=length)

        try:
            identity = getattr(brain, "self_model", None)
            if identity is not None:
                name = identity.get("name") or identity.get("identity") if isinstance(identity, dict) else None
                if name:
                    packet.identity = str(name)
        except Exception:  # noqa: BLE001 - best-effort
            pass

        try:
            belief = brain.identity.identity_for("person")
            packet.addressee = str(belief.name or "") if belief is not None else ""
        except Exception:  # noqa: BLE001
            pass

        try:
            situations = getattr(brain, "_last_situations", None) or []
            if situations:
                packet.current_situation = str(situations[0].get("label", ""))
        except Exception:  # noqa: BLE001
            pass

        with contextlib.suppress(Exception):
            packet.current_topic = str(brain.discourse.snapshot().get("topic", "") or "")

        # Task 5.4: memory entries are explainable (memory_id / why / source).
        with contextlib.suppress(Exception):
            from .retrieval_policy import RetrievalContext, RetrievalScorer

            candidates = []
            retrieve = getattr(brain.memory, "retrieve_indexed", getattr(brain.memory, "retrieve", None))
            if retrieve is not None:
                query = packet.current_topic or packet.current_situation or "memory"
                candidates = list(retrieve(query, limit=12))
            ctx = RetrievalContext(
                person=packet.addressee,
                situation=packet.current_situation,
                location=str((getattr(brain, "_spatial_context", lambda: {})() or {}).get("place", "") or ""),
            )
            scored = RetrievalScorer().rank(
                candidates,
                relevance_for=lambda idx, _r: 1.0 / (1 + idx),
                context=ctx,
                limit=MAX_MEMORY_ENTRIES,
            )
            packet.relevant_memory = [
                {
                    "memory_id": s.memory_id,
                    "content": str(getattr(s.record, "content", ""))[:300],
                    "why": ", ".join(s.why[:2]),
                    "confidence": round(s.score, 3),
                    "source": str(getattr(s.record, "verification_status", "unverified")),
                    "last_updated": str(getattr(s.record, "created_at", ""))[:19],
                }
                for s in scored
            ]

        with contextlib.suppress(Exception):
            packet.open_threads = [str(q) for q in brain.working_memory.unresolved_questions[:3]]

        with contextlib.suppress(Exception):
            entities = brain.unified_world.to_world_state().entities
            packet.current_perception = list(entities)[:8]

        with contextlib.suppress(Exception):
            social = getattr(brain.social_context, "snapshot", lambda: {})() if getattr(brain, "social_context", None) else {}
            packet.social_state = social

        packet.grounding_constraints = [
            "only use supplied evidence",
            "never invent world state, identity, or memories",
        ]
        return packet
