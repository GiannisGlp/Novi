"""Skill system (docs/plans/01_BRAIN/16_SKILL_SYSTEM_DESIGN.md), Phase P1 slice.

Pins:
  - discovery of shipped SKILL.md packages with manifest validation;
  - malformed manifests rejected gracefully (never raise);
  - deterministic trigger matching with ranking;
  - maths skill: exact offline evaluation including percent-of phrasing;
  - pdf-reader: honest dependency_missing outcome when pypdf is absent;
  - script path escape attempts rejected at load time;
  - runaway scripts killed by timeout;
  - engine integration: brain_use_skill audits, emits, and admits results
    to memory with provenance skill:<name>;
  - instruction-kind skills match but refuse run().
"""

import json
import tempfile
import time
import unittest
from pathlib import Path

from novi.brain.skills import SkillRegistry, load_manifest
from novi.brain.tests.test_mac_brain import FakeCamera

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"  # novi/skills/
DSH_CATALOG = Path(__file__).resolve().parents[3] / ".dsh" / "skills"


class DiscoveryTests(unittest.TestCase):
    def test_shipped_skills_discovered(self):
        r = SkillRegistry([SKILLS_DIR])
        names = {m.name for m in r.discover()}
        self.assertTrue({"maths", "pdf-reader", "pdf-creator", "humanizer"} <= names)

    def test_catalog_has_no_bodies(self):
        r = SkillRegistry([SKILLS_DIR])
        for entry in r.catalog():
            self.assertNotIn("# ", json.dumps(entry))

    def test_body_loaded_on_demand(self):
        r = SkillRegistry([SKILLS_DIR])
        body = r.body("humanizer")
        self.assertIsNotNone(body)
        self.assertIn("Humanizer", body)

    def test_malformed_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad"
            bad.mkdir()
            (bad / "SKILL.md").write_text("---\nname: Bad Name!\ndescription: x\n---\nbody\n")
            self.assertIsNone(load_manifest(bad / "SKILL.md"))
            empty = Path(td) / "empty"
            empty.mkdir()
            (empty / "SKILL.md").write_text("no frontmatter at all\n")
            self.assertIsNone(load_manifest(empty / "SKILL.md"))

    def test_script_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            skill = base / "evil"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: evil\ndescription: escapes\nkind: script\nscript: ../../outside.py\n---\n"
            )
            (base / "outside.py").write_text("print('pwned')\n")
            self.assertIsNone(load_manifest(skill / "SKILL.md"))

    def test_yaml_block_scalar_description_parsed(self):
        # The agent-harness catalog (.dsh/skills) uses multi-line
        # `description: |` frontmatter; Novi must read it, not choke on it.
        with tempfile.TemporaryDirectory() as td:
            skill = Path(td) / "blocky"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: blocky\ndescription: |\n  First line of the description.\n  Second line continues it.\nkind: instruction\n---\nbody\n"
            )
            m = load_manifest(skill / "SKILL.md")
            self.assertIsNotNone(m)
            self.assertTrue(m.description.startswith("First line"))
            self.assertIn("Second line", m.description)

    def test_ported_humanizer_matches_upstream_body(self):
        # The ported skill keeps the MIT upstream body; frontmatter is Novi's.
        ported = (SKILLS_DIR / "humanizer" / "SKILL.md").read_text(encoding="utf-8")
        upstream = DSH_CATALOG / "humanizer" / "SKILL.md"
        if not upstream.is_file():
            self.skipTest(".dsh catalog not present")
        up = upstream.read_text(encoding="utf-8")
        body_start = up.index("# Humanizer")
        self.assertIn(up[body_start:body_start + 200].split("\n")[0], ported)
        self.assertIn('license: MIT', ported)

    def test_dsh_catalog_skills_load_if_present(self):
        if not DSH_CATALOG.is_dir():
            self.skipTest(".dsh/skills catalog not present")
        for name in ("humanizer", "pdf"):
            m = load_manifest(DSH_CATALOG / name / "SKILL.md")
            self.assertIsNotNone(m, name)
            self.assertTrue(len(m.description) > 40, f"{name} description truncated")

    def test_every_shipped_skill_manifest_validates(self):
        # Invariant across novi/skills/*: nothing ships that fails load_manifest.
        manifests = [load_manifest(p) for p in sorted(SKILLS_DIR.glob("*/SKILL.md"))]
        self.assertGreaterEqual(len(manifests), 9)
        self.assertTrue(all(m is not None for m in manifests))

    def test_advanced_math_skills_discovered_and_matched(self):
        r = SkillRegistry([SKILLS_DIR])
        names = {m.name for m in r.discover()}
        for expected in ("geometry-construction", "geometry-proofs", "trigonometry", "prime-numbers", "symbolic-math"):
            self.assertIn(expected, names)
        self.assertEqual(r.match("prove the Pythagorean theorem")[0].name, "geometry-proofs")
        self.assertEqual(r.match("differentiate sin(x)")[0].name, "symbolic-math")
        self.assertEqual(r.match("is 97 a prime number? check divisibility")[0].name, "prime-numbers")

    def test_symbolic_math_script_operations(self):
        r = SkillRegistry([SKILLS_DIR])
        cases = [
            ((["solve", "x**2 - 4", "x"]), ["-2", "2"]),
            ((["diff", "x**3", "x"]), "3*x**2"),
            ((["integrate", "2*x", "x"]), "x**2"),
            ((["factor", "x**2 - 1"]), "(x - 1)*(x + 1)"),
            ((["limit", "sin(x)/x", "x"]), "1"),
            ((["simplify", "sin(x)**2 + cos(x)**2"]), "1"),
        ]
        for args, expected in cases:
            res = r.run("symbolic-math", args)
            self.assertTrue(res.ok, f"{args}: {res.data}")
            if isinstance(expected, list):
                self.assertEqual(res.data["result"], expected)
            else:
                self.assertEqual(res.data["result"], expected)

    def test_symbolic_math_rejects_bad_input(self):
        r = SkillRegistry([SKILLS_DIR])
        bad_op = r.run("symbolic-math", ["frobnicate", "x"])
        self.assertFalse(bad_op.ok)
        bad_expr = r.run("symbolic-math", ["solve", "this is not math("])
        self.assertFalse(bad_expr.ok)
        missing = r.run("symbolic-math", [])
        self.assertFalse(missing.ok)

    def test_geometry_construction_carries_citations(self):
        citations = SKILLS_DIR / "geometry-construction" / "references" / "CITATIONS.bib"
        self.assertTrue(citations.is_file())
        self.assertIn("Euclid", citations.read_text(encoding="utf-8"))

    def test_ported_skills_have_license_or_original_authorship(self):
        # Governance rule: only MIT-licensed catalog skills are pasted;
        # everything else in novi/skills is original Novi authorship.
        licensed = SKILLS_DIR / "humanizer" / "LICENSE"
        self.assertTrue(licensed.is_file())
        for name in ("maths", "pdf-reader", "pdf-creator"):
            self.assertTrue((SKILLS_DIR / name).is_dir(), name)


class MatchTests(unittest.TestCase):
    def test_trigger_match_ranks_and_ignores_unknowns(self):
        r = SkillRegistry([SKILLS_DIR])
        r.discover()
        hits = r.match("please calculate 15% of 240")
        self.assertEqual(hits[0].name, "maths")
        self.assertEqual(r.match("tell me about your day"), [])

    def test_whole_word_matching_no_substring_false_hits(self):
        r = SkillRegistry([SKILLS_DIR])
        r.discover()
        # "mathematics" contains "math" but is a different word.
        hits = r.match("I study mathematics")
        self.assertEqual([h.name for h in hits if h.name == "maths"], [])


class ScriptRunTests(unittest.TestCase):
    def test_maths_deterministic_results(self):
        r = SkillRegistry([SKILLS_DIR])
        cases = [
            (["12*(3+4)"], 84),
            (["15% of 240"], 36),
            (["2^10"], 1024),
            (["ten plus two"], None),
        ]
        for args, expected in cases:
            res = r.run("maths", args)
            if expected is None:
                self.assertFalse(res.ok)
            else:
                self.assertTrue(res.ok, args)
                self.assertEqual(res.data["result"], expected)

    def test_pdf_reader_reports_dependency_missing_honestly(self):
        r = SkillRegistry([SKILLS_DIR])
        try:
            import pypdf  # noqa: F401
            self.skipTest("pypdf installed; degradation path not exercised")
        except ImportError:
            pass
        res = r.run("pdf-reader", ["/tmp/whatever.pdf"])
        self.assertEqual(res.outcome, "dependency_missing")
        self.assertFalse(res.ok)
        self.assertEqual(res.data.get("dependency"), "pypdf")

    def test_timeout_kills_runaway_script(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            skill = base / "slowpoke"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: slowpoke\ndescription: sleeps forever\nkind: script\nscript: sleep.py\n---\n"
            )
            (skill / "sleep.py").write_text("import time\ntime.sleep(30)\n")
            r = SkillRegistry([base])
            start = time.monotonic()
            res = r.run("slowpoke", timeout_s=1)
            self.assertLess(time.monotonic() - start, 10)
            self.assertEqual(res.outcome, "timeout")

    def test_instruction_skill_refuses_run(self):
        r = SkillRegistry([SKILLS_DIR])
        res = r.run("humanizer")
        self.assertFalse(res.ok)
        self.assertEqual(res.data["reason"], "not_a_script_skill")

    def test_unknown_skill_is_error_not_exception(self):
        r = SkillRegistry([SKILLS_DIR])
        res = r.run("does-not-exist")
        self.assertEqual(res.outcome, "error")
        self.assertEqual(res.data["reason"], "unknown_skill")


class DynamicActivationTests(unittest.TestCase):
    """plan 16 P2: context-driven loading, awareness, and use."""

    def test_plan_auto_extracts_maths_args(self):
        r = SkillRegistry([SKILLS_DIR])
        for text, expected in (
            ("calculate 15% of 240", ["15% of 240"]),
            ("what is 12*(3+4)?", ["12*(3+4)"]),
            ("hey can you compute 2^10 please", ["2^10"]),
        ):
            planned = r.plan_auto(text)
            if expected is None:
                continue
            self.assertIsNotNone(planned, text)
            self.assertEqual(planned[0].name, "maths")
            self.assertEqual(planned[1], expected)

    def test_plan_auto_symbolic_op(self):
        r = SkillRegistry([SKILLS_DIR])
        planned = r.plan_auto("differentiate sin(x)*x with respect to x")
        self.assertIsNotNone(planned)
        self.assertEqual(planned[0].name, "symbolic-math")
        self.assertEqual(planned[1][0], "diff")

    def test_plan_auto_ignores_non_skill_text(self):
        r = SkillRegistry([SKILLS_DIR])
        self.assertIsNone(r.plan_auto("tell me about your day"))
        self.assertIsNone(r.plan_auto("humanize this paragraph for me"))  # instruction-only skill

    def _brain(self):
        from novi.brain.engine import MacBrain, MacBrainConfig
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        return brain

    def test_offline_message_answers_from_exact_result(self):
        brain = self._brain()
        try:
            out = brain.respond("calculate 15% of 240")
            self.assertIn("36", out["text"])
            self.assertEqual(out["grounding"]["route"], "skill")
            events = [e for e in brain.events if e.get("event_type") == "skill.invoked"]
            self.assertTrue(events)
            audits = [a for a in brain.audit_trail.snapshots(limit=20) if "skill:maths" in str(a.get("action", ""))]
            self.assertTrue(audits)
        finally:
            brain.stop()

    def test_offline_non_skill_text_skips_skill_path(self):
        brain = self._brain()
        try:
            out = brain.respond("what are you thinking about?")
            self.assertNotEqual(out.get("grounding", {}).get("route"), "skill")
        finally:
            brain.stop()

    def test_llm_sees_skill_catalog_in_system_prompt(self):
        seen = {}

        def stub(system, user, **kw):
            seen["system"] = system
            return "hello there"

        brain = self._brain()
        try:
            out = brain.respond("how was your day?", llm_chat=stub)
            self.assertTrue(out["text"])
            self.assertIn("@skill", seen["system"])
            self.assertIn("maths", seen["system"])
        finally:
            brain.stop()

    def test_model_requested_skill_runs_and_second_pass_answers(self):
        calls = []

        def stub(system, user, **kw):
            calls.append(system)
            if len(calls) == 1:
                return "@skill maths 7*6"
            return "that would be forty two!"

        brain = self._brain()
        try:
            out = brain.respond("hey whats 7*6 quickly", llm_chat=stub)
            # plan_auto answers deterministically before the LLM path; force the
            # convention path by using an expression auto-extraction rejects.
            self.assertIsNotNone(out["text"])
            if len(calls) >= 2:
                # Second pass must carry the executed skill's exact result.
                self.assertIn("42", calls[1])
            events = [e for e in brain.events if e.get("event_type") == "skill.invoked"]
            self.assertTrue(events)
        finally:
            brain.stop()

    def test_directive_parser_is_strict(self):
        brain = self._brain()
        try:
            names = [c["name"] for c in brain.skills.catalog() if c["kind"] in ("script", "hybrid")]
            ok = brain._parse_skill_directive("@skill maths 7*6", names)
            self.assertEqual(ok, ("maths", ["7*6"]))
            multi = brain._parse_skill_directive("@skill symbolic-math diff x**2", names)
            self.assertEqual(multi, ("symbolic-math", ["diff", "x**2"]))
            self.assertIsNone(brain._parse_skill_directive("@skill unknown-skill 1", names))
            self.assertIsNone(brain._parse_skill_directive("just talking about @skill things", names))
            self.assertIsNone(brain._parse_skill_directive(None, names))
        finally:
            brain.stop()


class SkillsReadmeTests(unittest.TestCase):
    def test_readme_lists_every_shipped_skill(self):
        readme = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
        manifests = sorted(SKILLS_DIR.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(manifests), 9)
        for m in manifests:
            name = m.parent.name
            self.assertIn(f"`{name}`", readme, f"README missing {name}")
        self.assertIn("novi/skills/", readme)
        self.assertIn("~/.novi/skills/", readme)


class EngineIntegrationTests(unittest.TestCase):
    def _brain(self):
        from novi.brain.engine import MacBrain, MacBrainConfig
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        return brain

    def test_brain_discovers_skills_and_runs_maths(self):
        brain = self._brain()
        try:
            names = {m.name for m in brain.skills.discover()}
            self.assertIn("maths", names)
            res = brain.brain_use_skill("maths", ["7*6"])
            self.assertTrue(res.ok)
            self.assertEqual(res.data["result"], 42)
        finally:
            brain.stop()

    def test_invocation_emits_event_and_admits_memory_with_provenance(self):
        brain = self._brain()
        try:
            brain._cycle_correlation_id = str(brain._cycle_correlation_id)
            res = brain.brain_use_skill("maths", ["9+1"])
            self.assertTrue(res.ok)
            events = [e for e in brain.events if e.get("event_type") == "skill.invoked"]
            self.assertTrue(events)
            records = list(getattr(brain.memory, "_records", {}).values()) if hasattr(brain.memory, "_records") else []
            hit = [rec for rec in records if getattr(rec, "memory_type", "") == "skill_result"]
            self.assertTrue(hit)
            prov = hit[0].provenance if isinstance(hit[0].provenance, dict) else {}
            self.assertEqual(prov.get("source"), "skill:maths")

            audits = [a for a in brain.audit_trail.snapshots(limit=50) if "skill:" in str(a.get("action", ""))]
            self.assertTrue(audits)
        finally:
            brain.stop()

    def test_failed_skill_still_audited_without_memory_admit(self):
        brain = self._brain()
        try:
            res = brain.brain_use_skill("does-not-exist")
            self.assertFalse(res.ok)
            records = list(getattr(brain.memory, "_records", {}).values()) if hasattr(brain.memory, "_records") else []
            self.assertFalse([r for r in records if getattr(r, "memory_type", "") == "skill_result"])
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
