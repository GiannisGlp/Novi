"""LLM-assisted knowledge-triple extraction (gap-audit plan Phase D3).

Asks the local model (Ollama) to emit constrained-JSON triples from episodic
text, validates them hard, and falls back to the deterministic regex extractor
whenever the LLM path is unavailable or its output is rejected.

Boundaries honored (docs/03-cognition, docs/04):
  - The FORBIDDEN guard (dialogue rule 8) rejects any model response matching
    assistant-speak patterns before parsing — the model never talks *through*
    the extraction path.
  - Extracted triples are hypotheses: they enter EntityKnowledgeGraph with
    evidence-backed confidence and contradiction handling, never as facts.
  - Fully deterministic when no transport is configured (regex fallback only).
"""

from __future__ import annotations

import json
import re
from typing import Callable, Iterable

ALLOWED_PREDICATES = frozenset({
    "in", "on", "near", "has", "is", "likes", "owns", "moved", "carried",
    "tends", "followed", "located_near", "related_to", "part_of", "made_of",
})

_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{1,28}$")


def _norm_entity(value: str) -> str:
    v = str(value).strip().lower()
    return re.sub(r"\s+", "_", v)


class LLMTripleExtractor:
    """Constrained-JSON triple extraction with a FORBIDDEN-guard gate."""

    def __init__(self, *, max_triples: int = 5) -> None:
        self.max_triples = int(max_triples)

    # ---- prompt ----

    def system_prompt(self) -> str:
        return (
            "You extract entity-relation-entity triples from a sentence. "
            "Reply with ONLY a JSON array like "
            '[{"subject":"cup","predicate":"on","object":"table"}]. '
            "Rules: lowercase single words or snake_case; predicates limited to: "
            + ", ".join(sorted(ALLOWED_PREDICATES))
            + ". No prose, no explanations."
        )

    def user_prompt(self, text: str, entities: Iterable[str]) -> str:
        return f"Sentence: {text}\nKnown entities: {', '.join(entities)}"

    # ---- validation ----

    def _forbidden(self, raw: str) -> bool:
        """Rule 8 gate: assistant-speak in the response rejects it entirely."""
        from .dialogue import _FORBIDDEN
        return any(p.search(raw or "") for p in _FORBIDDEN)

    def parse(self, raw: str) -> list[tuple[str, str, str]]:
        """Parse and validate constrained JSON; invalid output yields []."""
        if not raw or not raw.strip():
            return []
        candidate = raw.strip()
        # Tolerate code fences / leading prose by grabbing the outermost array.
        match = re.search(r"\[.*\]", candidate, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        out: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for row in data[: self.max_triples * 2]:
            if not isinstance(row, dict):
                continue
            s = _norm_entity(row.get("subject", ""))
            p = _norm_entity(row.get("predicate", ""))
            o = _norm_entity(row.get("object", ""))
            if not (_TOKEN_RE.match(s) and _TOKEN_RE.match(o)):
                continue
            if p not in ALLOWED_PREDICATES:
                continue
            key = (s, p, o)
            if key in seen or s == o:
                continue
            seen.add(key)
            out.append(key)
            if len(out) >= self.max_triples:
                break
        return out

    def extract(
        self,
        text: str,
        entity_refs: tuple[str, ...],
        *,
        llm_chat: Callable[..., str | None] | None,
    ) -> list[tuple[str, str, str]]:
        """Extract triples via ``llm_chat`` transport; [] when unavailable/rejected."""
        if llm_chat is None or not (text or "").strip():
            return []
        try:
            raw = llm_chat(system=self.system_prompt(), user=self.user_prompt(text, entity_refs))
        except Exception:  # noqa: BLE001 - transport failures fall back to regex
            return []
        if raw is None:
            return []
        if self._forbidden(raw):
            return []
        known = {e.lower() for e in entity_refs}
        triples = self.parse(raw)
        if not known:
            return triples
        # Ground the extraction: at least one endpoint must be a known
        # entity, so the model can extend knowledge ("table in kitchen")
        # but cannot invent entities from nothing.
        return [(s, p, o) for (s, p, o) in triples if s in known or o in known]
