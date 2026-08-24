"""Skill system for Novi (design doc: docs/plans/01_BRAIN/16_SKILL_SYSTEM_DESIGN.md).

Loads portable ``SKILL.md`` packages — the same shape used by coding-agent
harnesses (YAML-lite frontmatter: name/description/kind/triggers, markdown
instructions, optional bundled script) — and runs them inside Novi's
governance boundaries:

  - progressive disclosure: only manifests stay resident; bodies load on use;
  - deterministic trigger matching (no model needed to decide *whether* a
    skill applies);
  - script skills execute through one allowlisted interpreter with a hard
    timeout and JSON-on-stdout contract;
  - every invocation is auditable by the caller via AuditTrail;
  - honest degradation: missing optional dependencies are reported as
    structured outcomes, never silently swallowed.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_TIMEOUT_S = 20


@dataclass(frozen=True)
class SkillManifest:
    """Frontmatter of a SKILL.md — the only part kept resident."""

    name: str
    description: str
    kind: str  # "instruction" | "script" | "hybrid"
    triggers: tuple[str, ...]
    script: str | None  # relative path to bundled script, if any
    path: Path  # SKILL.md location

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "kind": self.kind,
            "triggers": list(self.triggers),
        }


_FRONT_KEYS = ("name", "description", "kind", "triggers", "script")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,39}$")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the YAML-lite block between leading --- fences (key: value)."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" not in line or (line[:1].isspace() and not out):
            break
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value in ("|", "|-", "|+", ">", ">-", ">+"):  # YAML block/folded scalar
            block: list[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    block.append("")  # blank lines inside a block are content
                    i += 1
                    continue
                if nxt[:1].isspace():
                    block.append(nxt.strip())
                    i += 1
                    continue
                break
            if key in _FRONT_KEYS:
                out[key] = " ".join(part for part in " ".join(block).split(" ") if part).strip()
            continue
        i += 1
        if key in _FRONT_KEYS:
            out[key] = value
    return out


def _parse_triggers(raw: str) -> tuple[str, ...]:
    return tuple(t.strip().lower() for t in raw.split(",") if t.strip())


def load_manifest(path: Path) -> SkillManifest | None:
    """Load and validate one SKILL.md; None when invalid (never raises)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = parse_frontmatter(text)
    name = fm.get("name", "")
    description = fm.get("description", "")
    if not _NAME_RE.match(name) or not description:
        return None
    kind = fm.get("kind", "instruction").lower()
    if kind not in ("instruction", "script", "hybrid"):
        return None
    script = fm.get("script") or None
    if kind in ("script", "hybrid"):
        if not script:
            return None
        script_path = (path.parent / script).resolve()
        try:
            script_path.relative_to(path.parent.resolve())
        except ValueError:
            return None  # script must live inside the skill directory
        if not script_path.is_file():
            return None
    return SkillManifest(
        name=name,
        description=description,
        kind=kind,
        triggers=_parse_triggers(fm.get("triggers", "")),
        script=script,
        path=path,
    )


@dataclass
class SkillRunResult:
    skill: str
    ok: bool
    outcome: str  # "completed" | "dependency_missing" | "timeout" | "error"
    data: dict[str, Any] = field(default_factory=dict)


def _trigger_in_words(trigger: str, words: list[str]) -> bool:
    """True when the trigger's word sequence appears contiguously."""
    seq = trigger.split("-") if "-" in trigger else [trigger]
    n = len(seq)
    return any(words[i:i + n] == seq for i in range(len(words) - n + 1))


class SkillRegistry:
    """Discovers SKILL.md packages and executes script skills safely."""

    def __init__(self, dirs: list[Path | str]) -> None:
        self._dirs = [Path(d) for d in dirs]
        self._skills: dict[str, SkillManifest] = {}
        self._discovered = False

    # ---- discovery (progressive disclosure: manifests only) ----

    def discover(self) -> list[SkillManifest]:
        self._skills.clear()
        found: list[SkillManifest] = []
        seen_dirs = set()
        for base in self._dirs:
            if not base.is_dir() or str(base.resolve()) in seen_dirs:
                continue
            seen_dirs.add(str(base.resolve()))
            for skill_md in sorted(base.glob("*/SKILL.md")):
                m = load_manifest(skill_md)
                if m is not None and m.name not in self._skills:
                    self._skills[m.name] = m
                    found.append(m)
        self._discovered = True
        return found

    def _ensure_discovered(self) -> None:
        if not self._discovered:
            self.discover()

    def get(self, name: str) -> SkillManifest | None:
        self._ensure_discovered()
        return self._skills.get(str(name).lower())

    def catalog(self) -> list[dict[str, Any]]:
        """Manifest snapshots for prompts/UI — never the full bodies."""
        self._ensure_discovered()
        return [m.snapshot() for m in sorted(self._skills.values(), key=lambda m: m.name)]

    def body(self, name: str) -> str | None:
        """Full instructions, loaded only on activation."""
        m = self.get(name)
        if m is None:
            return None
        try:
            return m.path.read_text(encoding="utf-8")
        except OSError:
            return None

    # ---- deterministic matching ----

    def match(self, text: str) -> list[SkillManifest]:
        """Rank skills whose triggers appear as whole words in ``text``.

        Multi-word/hyphenated triggers ("go-to-market") match their word
        sequence contiguously, so they work despite tokenization.
        """
        self._ensure_discovered()
        words = re.findall(r"[a-z0-9]+", text.lower())
        scored: list[tuple[int, int, str, SkillManifest]] = []
        for m in self._skills.values():
            matched = [t for t in m.triggers if _trigger_in_words(t, words)]
            if not matched:
                continue
            # Longer triggers are more specific intents; they outrank shorter
            # ones, then more hits, then alphabetical name for determinism.
            best_len = max(len(t) for t in matched)
            scored.append((-best_len, -len(matched), m.name, m))
        scored.sort(key=lambda s: (s[0], s[1], s[2]))
        return [m for _, _, _, m in scored]

    # ---- script execution ----

    def run(self, name: str, args: list[str] | None = None, *, timeout_s: int = SCRIPT_TIMEOUT_S) -> SkillRunResult:
        """Execute a script/hybrid skill through the allowlisted interpreter."""
        m = self.get(name)
        if m is None:
            return SkillRunResult(skill=str(name), ok=False, outcome="error", data={"reason": "unknown_skill"})
        if m.kind == "instruction" or not m.script:
            return SkillRunResult(skill=m.name, ok=False, outcome="error", data={"reason": "not_a_script_skill"})
        script_path = (m.path.parent / m.script).resolve()
        cmd = [sys.executable, str(script_path), *[str(a) for a in (args or [])]]
        try:
            proc = subprocess.run(  # noqa: S603 - fixed interpreter, validated script path
                cmd, capture_output=True, text=True, timeout=max(1, int(timeout_s)), cwd=str(m.path.parent),
            )
        except subprocess.TimeoutExpired:
            return SkillRunResult(skill=m.name, ok=False, outcome="timeout", data={"timeout_s": timeout_s})
        except OSError as exc:
            return SkillRunResult(skill=m.name, ok=False, outcome="error", data={"reason": str(exc)})
        stdout = (proc.stdout or "").strip()
        # Structured errors first: a script may print {"ok": false, ...} and
        # exit nonzero; honor its JSON over the raw stderr blob.
        if stdout:
            try:
                payload = json.loads(stdout)
                if isinstance(payload, dict) and payload.get("ok") is False:
                    outcome = "dependency_missing" if payload.get("outcome") == "dependency_missing" else "error"
                    return SkillRunResult(skill=m.name, ok=False, outcome=outcome, data=payload)
            except ValueError:
                pass
        if proc.returncode != 0:
            return SkillRunResult(
                skill=m.name, ok=False, outcome="error",
                data={"returncode": proc.returncode, "stderr": (proc.stderr or "")[-400:]},
            )
        try:
            payload = json.loads(stdout)
            if not isinstance(payload, dict):
                raise ValueError("payload_not_object")
        except ValueError:
            return SkillRunResult(
                skill=m.name, ok=False, outcome="error",
                data={"reason": "script_must_emit_json_object"},
            )
        if payload.get("outcome") == "dependency_missing":
            return SkillRunResult(skill=m.name, ok=False, outcome="dependency_missing", data=payload)
        return SkillRunResult(skill=m.name, ok=True, outcome="completed", data=payload)

    # ---- dynamic activation (plan 16 P2): context-triggered planning ----

    def plan_auto(self, text: str) -> tuple[SkillManifest, list[str]] | None:
        """Plan a skill run from conversation text alone — no model involved.

        Returns ``(manifest, args)`` for the first script/hybrid skill whose
        triggers match AND whose argument extractor finds a confident argument,
        or None. The caller executes it through governed invocation.
        """
        self._ensure_discovered()
        stripped = text.strip().rstrip("?!. ")
        for m in self.match(stripped)[:3]:
            if m.kind not in ("script", "hybrid") or not m.script:
                continue
            extractor = _ARG_EXTRACTORS.get(m.name)
            if extractor is None:
                continue
            args = extractor(stripped)
            if args:
                return m, args
        # No trigger word hit: still probe symbolic-math when the message is
        # clearly question-shaped ("what is 12*(3+4)?") so plain arithmetic
        # works without keyword scaffolding.
        sym = self.get("symbolic-math")
        if sym is not None and _MATH_QUESTION_SHAPE.match(stripped):
            args = _extract_maths_args(stripped)
            if args:
                return sym, ["solve", *args]
        return None


_MATH_SCAFFOLD = re.compile(
    r"^(?:hey|hi|ok|okay|so|novi[, ]+|can you|could you|please|tell me|i need|i want)"
    r"[\s,:]+",
    re.IGNORECASE,
)
_MATH_TAIL = re.compile(r"(?:\s*(?:please|thanks|thank you))+[?!.\s]*$|\s+$", re.IGNORECASE)
_MATH_LEAD = re.compile(
    r"^(?:what(?:'s| is| are)|how much (?:is|are)|how many|calculate|compute|"
    r"evaluate|work out|figure out|solve|do the math(?:s)? (?:for|on)|math:)\s*",
    re.IGNORECASE,
)
_MATH_QUESTION_SHAPE = re.compile(
    r"^\s*(?:what|how much|how many|calculate|compute|evaluate|solve|work out|figure out)\b",
    re.IGNORECASE,
)


def _extract_maths_args(text: str) -> list[str] | None:
    """Pull an arithmetic expression out of a request phrase."""
    t = text.strip()
    prev = None
    while prev != t:
        prev = t
        t = _MATH_SCAFFOLD.sub("", t, count=1)
        t = _MATH_LEAD.sub("", t, count=1).strip()
        t = _MATH_TAIL.sub("", t)
    t = t.strip()
    if not t or not any(c.isdigit() for c in t):
        return None
    if len(t) > 120:
        return None
    return [t]


_SYMBOLIC_OPS: dict[str, str] = {
    "differentiate": "diff",
    "derivative": "diff",
    "derive": "diff",
    "integrate": "integrate",
    "integral": "integrate",
    "antiderivative": "integrate",
    "simplify": "simplify",
    "expand": "expand",
    "factor": "factor",
    "factorize": "factor",
    "factorise": "factor",
}


def _extract_symbolic_args(text: str) -> list[str] | None:
    """Detect a symbolic op word and extract the expression after it."""
    lowered = text.lower()
    for word, op in _SYMBOLIC_OPS.items():
        idx = lowered.find(word)
        if idx == -1:
            continue
        rest = text[idx + len(word):].strip()
        rest = re.sub(r"^(?:of|the|expression)?\s*", "", rest).rstrip("?!. ")
        if not rest:
            return None
        # A variable may be given as "... with respect to y".
        var = "x"
        wm = re.search(r"\bwith respect to\s+([a-zA-Z])\b\s*$", rest)
        if wm:
            var = wm.group(1)
            rest = rest[: wm.start()].strip()
        rest = rest.removeprefix("d/dx ").strip()
        if not rest:
            return None
        args = [op, rest]
        if op in ("diff", "integrate") and var != "x":
            args.append(var)
        return args
    return None


# Per-skill argument extractors for plan_auto (skill name → extractor).
def _extract_symbolic_math_args(text: str) -> list[str] | None:
    """Symbolic-math handles both op-keyword requests and plain arithmetic."""
    symbolic = _extract_symbolic_args(text)
    if symbolic is not None:
        return symbolic
    arithmetic = _extract_maths_args(text)
    if arithmetic is not None:
        return ["solve", *arithmetic]
    return None


_ARG_EXTRACTORS: dict[str, Any] = {
    "symbolic-math": _extract_symbolic_math_args,
}
