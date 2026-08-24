"""Centralized skill activation — owned by the brain, not by chat.

Plan 16 P4: skill relevance is decided in ONE place that wraps every Novi
response surface. The engine constructs a ``SkillActivator`` next to its
``SkillRegistry``; every producer of content (chat replies today, other
surfaces later) asks the activator what applies instead of implementing its
own matching. Three sources feed it:

1. **Utterance/discourse** — matched per reply.
2. **Knowledge & memory context** — recent facts, recall results, history.
3. **Cycle observation** — perception detections, recalled memories and the
   situation narrative prime skills proactively each engine cycle
   (``skill.primed`` events), decaying after ``prime_ttl_cycles``.

The humanizer style pass is special-cased here too: it is an unconditional,
process-cached block for every composed user-facing reply, never occupying a
matched-guidance slot.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from novi.brain.skills import SkillManifest, SkillRegistry

_EMITTER = Callable[[str, dict[str, Any]], None]


@dataclass
class _PrimedSkill:
    name: str
    source: str
    cycle: int
    primed_at: float = field(default_factory=time.monotonic)


class SkillActivator:
    """Decides which skills apply to whatever Novi is about to do."""

    def __init__(
        self,
        registry: SkillRegistry | None,
        *,
        emit: _EMITTER | None = None,
        prime_ttl_cycles: int = 10,
        max_primed: int = 4,
    ) -> None:
        self._registry = registry
        self._emit: _EMITTER = emit or (lambda event, payload: None)
        self.prime_ttl_cycles = prime_ttl_cycles
        self.max_primed = max_primed
        self._primed: dict[str, _PrimedSkill] = {}
        self._style_block_cache: str | None = None

    # ------------------------------------------------------------------ #
    # Matching sources
    # ------------------------------------------------------------------ #

    def _candidates_for(self, grounding_text: str, memory_text: str = "") -> list[SkillManifest]:
        """Manifests relevant to the given contexts, deduped, best first."""
        if self._registry is None:
            return []
        ordered: list[SkillManifest] = []
        seen_ids: set[int] = set()
        for source in (grounding_text, memory_text):
            if not source or not source.strip():
                continue
            for m in self._registry.match(source):
                if id(m) not in seen_ids:
                    seen_ids.add(id(m))
                    ordered.append(m)
        for name in self.primed_names():
            m = self._registry.get(name)
            if m is not None and id(m) not in seen_ids:
                seen_ids.add(id(m))
                ordered.append(m)
        return ordered

    def guidance_for(
        self,
        grounding_text: str,
        memory_text: str = "",
        *,
        max_skills: int = 2,
        char_budget: int = 1600,
        exclude: tuple[str, ...] = (),
    ) -> tuple[str, list[str]]:
        """Prompt-guidance block for instruction skills relevant right now.

        Considers the utterance, memory context, and cycle-primed skills;
        loads bodies on demand and clips each to ``char_budget`` at a line
        boundary. Returns ``(prompt_block, applied_names)``.
        """
        parts: list[str] = []
        applied: list[str] = []
        for m in self._candidates_for(grounding_text, memory_text):
            if m.kind != "instruction" or m.name in exclude or m.name in applied:
                continue  # script/hybrid act through execution paths
            body = self._registry.body(m.name) if self._registry else None
            if not body:
                continue
            clipped = body[:char_budget]
            if len(body) > char_budget:
                cut = body.rfind("\n", 0, char_budget)
                if cut > 200:
                    clipped = body[:cut]
            parts.append(
                f"### Skill guidance: {m.name}\n{clipped}\n"
                "Apply this guidance when it is relevant to answering; ignore what is not."
            )
            applied.append(m.name)
            if len(applied) >= max_skills:
                break
        if not parts:
            return "", []
        header = (
            "Relevant skills activated by this conversation — follow their "
            "guidance where it applies to your reply:\n\n"
        )
        return header + "\n".join(parts), applied

    # ------------------------------------------------------------------ #
    # Always-on humanizer style pass
    # ------------------------------------------------------------------ #

    def style_pass_block(self) -> str:
        """Unconditional humanizer core for every composed user-facing reply."""
        if self._registry is None:
            return ""
        if self._style_block_cache is not None:
            return self._style_block_cache
        body = self._registry.body("humanizer")
        if not body:
            self._style_block_cache = ""
            return ""
        start = body.find("# Humanizer")
        cut_at = body.find("## Content patterns")
        core = body[start:cut_at] if (start != -1 and cut_at > start) else body[:1600]
        self._style_block_cache = (
            "Style pass — ALWAYS apply this rewriting guidance to your final "
            "reply (decide it silently; never mention it):\n\n" + core.strip()
        )
        return self._style_block_cache

    # ------------------------------------------------------------------ #
    # Cycle-time priming (event-driven, decaying)
    # ------------------------------------------------------------------ #

    def observe_cycle(
        self,
        *,
        cycle: int,
        detections: list[str] | tuple[str, ...] = (),
        memories: list[str] | tuple[str, ...] = (),
        narrative: str = "",
        heard: str = "",
    ) -> list[str]:
        """Prime instruction skills from what this cycle saw/heard/recalled."""
        if self._registry is None:
            return []
        context_bits = [str(d)[:120] for d in detections if d]
        context_bits += [str(m)[:200] for m in memories if m]
        if narrative:
            context_bits.append(str(narrative)[:400])
        if heard:
            context_bits.append(str(heard)[:400])
        if not context_bits:
            return []
        text = "; ".join(context_bits)
        newly: list[str] = []
        for m in self._registry.match(text):
            if m.kind != "instruction" or m.name == "humanizer":
                continue  # humanizer is unconditional, never "primed"
            if m.name not in self._primed:
                self._primed[m.name] = _PrimedSkill(name=m.name, source="cycle_context", cycle=cycle)
                newly.append(m.name)
        while len(self._primed) > self.max_primed:
            oldest = min(self._primed.values(), key=lambda p: p.primed_at)
            del self._primed[oldest.name]
        if newly:
            self._emit("skill.primed", {"cycle": cycle, "skills": newly})
        return newly

    def expire(self, cycle: int) -> list[str]:
        """Drop primes older than the TTL window."""
        stale = [
            name
            for name, p in self._primed.items()
            if cycle - p.cycle > self.prime_ttl_cycles
        ]
        for name in stale:
            del self._primed[name]
        return stale

    def primed_names(self) -> list[str]:
        return sorted(self._primed)

    def prime_source(self, name: str) -> str | None:
        p = self._primed.get(name)
        return p.source if p else None


def build_activator(
    registry: SkillRegistry | None,
    emit: _EMITTER | None = None,
) -> SkillActivator:
    """Convenience constructor used by the engine."""
    return SkillActivator(registry, emit=emit)
