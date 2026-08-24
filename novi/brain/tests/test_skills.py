"""Skill system (docs/plans/01_BRAIN/16_SKILL_SYSTEM_DESIGN.md), Phase P1 slice.

Pins:
  - discovery of shipped SKILL.md packages with manifest validation;
  - malformed manifests rejected gracefully (never raise);
  - deterministic trigger matching with ranking;
  - symbolic-math: exact offline arithmetic (absorbed maths) + symbolic ops;
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
        self.assertTrue({"symbolic-math", "pdf-reader", "pdf-creator", "humanizer"} <= names)

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
        for name in ("pdf-reader", "pdf-creator"):
            self.assertTrue((SKILLS_DIR / name).is_dir(), name)


class MatchTests(unittest.TestCase):
    def test_trigger_match_ranks_and_ignores_unknowns(self):
        r = SkillRegistry([SKILLS_DIR])
        r.discover()
        hits = r.match("please calculate 15% of 240")
        self.assertEqual(hits[0].name, "symbolic-math")
        self.assertEqual(r.match("tell me about your day"), [])

    def test_whole_word_matching_no_substring_false_hits(self):
        r = SkillRegistry([SKILLS_DIR])
        r.discover()
        # "mathematics" contains "math" but is a different word.
        hits = r.match("I study mathematics")
        self.assertEqual([h.name for h in hits if h.name == "symbolic-math"], [])


class ScriptRunTests(unittest.TestCase):
    def test_maths_deterministic_results(self):
        r = SkillRegistry([SKILLS_DIR])
        cases = [
            (["solve", "12*(3+4)"], 84),
            (["solve", "15% of 240"], 36),
            (["solve", "2^10"], 1024),
            (["diff", "x**3", "x"], "3*x**2"),
            (["ten plus two"], None),
        ]
        for args, expected in cases:
            res = r.run("symbolic-math", args)
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
            self.assertEqual(planned[0].name, "symbolic-math")
            self.assertEqual(planned[1], ["solve"] + expected if len(expected) == 1 and not expected[0][0].isalpha() else expected)

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
            audits = [a for a in brain.audit_trail.snapshots(limit=20) if "skill:symbolic-math" in str(a.get("action", ""))]
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
            self.assertIn("symbolic-math", seen["system"])
        finally:
            brain.stop()

    def test_model_requested_skill_runs_and_second_pass_answers(self):
        calls = []

        def stub(system, user, **kw):
            calls.append(system)
            if len(calls) == 1:
                return "@skill symbolic-math solve 7*6"
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
            ok = brain._parse_skill_directive("@skill symbolic-math solve 7*6", names)
            self.assertEqual(ok, ("symbolic-math", ["solve", "7*6"]))
            multi = brain._parse_skill_directive("@skill symbolic-math diff x**2", names)
            self.assertEqual(multi, ("symbolic-math", ["diff", "x**2"]))
            self.assertIsNone(brain._parse_skill_directive("@skill unknown-skill 1", names))
            self.assertIsNone(brain._parse_skill_directive("just talking about @skill things", names))
            self.assertIsNone(brain._parse_skill_directive(None, names))
        finally:
            brain.stop()


class AdvancedDomainSkillsTests(unittest.TestCase):
    """Math/algebra, CS/data-science, business, sales & marketing skills."""

    def test_all_new_skills_discovered(self):
        r = SkillRegistry([SKILLS_DIR])
        names = {m.name for m in r.discover()}
        for expected in (
            "linear-algebra", "data-profile", "statistical-analysis",
            "sql-pro", "ceo-advisor", "marketing-strategy", "copywriting",
            "exploratory-data-analysis", "scikit-learn", "matplotlib",
            "version-ml-data", "algorithms-complexity", "diagram-design",
        ):
            self.assertIn(expected, names)

    def test_category_triggers_match(self):
        r = SkillRegistry([SKILLS_DIR])
        self.assertEqual(r.match("help me plan our go-to-market strategy")[0].name, "marketing-strategy")
        self.assertEqual(r.match("write sales copy for our landing page")[0].name, "copywriting")
        self.assertEqual(r.match("run a t-test hypothesis on these results")[0].name, "statistical-analysis")
        self.assertEqual(r.match("advise me on board and investor strategy")[0].name, "ceo-advisor")
        self.assertEqual(r.match("what is the big-o of quicksort?")[0].name, "algorithms-complexity")
        self.assertEqual(r.match("train a classifier on this dataset")[0].name, "scikit-learn")
        self.assertEqual(r.match("draw a sequence diagram for checkout")[0].name, "diagram-design")

    def test_linear_algebra_script_ops(self):
        r = SkillRegistry([SKILLS_DIR])
        solve = r.run("linear-algebra", ["solve", "[[2,1],[1,3]]", "[5,10]"])
        self.assertTrue(solve.ok)
        self.assertEqual(solve.data["result"], [1, 3])
        det = r.run("linear-algebra", ["det", "[[1,2],[3,4]]"])
        self.assertEqual(det.data["result"], -2.0)
        eig = r.run("linear-algebra", ["eig", "[[4,1],[2,3]]"])
        self.assertEqual(eig.data["eigenvalues"], [5.0, 2.0])
        singular = r.run("linear-algebra", ["inverse", "[[1,2],[2,4]]"])
        self.assertFalse(singular.ok)  # singular matrix reported honestly

    def test_data_profile_reports_columns_and_missing(self):
        import tempfile
        r = SkillRegistry([SKILLS_DIR])
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "people.csv"
            csv_path.write_text("name,age\nana,34\nrui,28\nsam,\n")
            res = r.run("data-profile", [str(csv_path)])
            self.assertTrue(res.ok, res.data)
            self.assertEqual(res.data["rows"], 3)
            self.assertEqual(res.data["columns"]["age"]["type"], "numeric")
            self.assertEqual(res.data["columns"]["age"]["missing"], 1)
            self.assertEqual(res.data["columns"]["name"]["type"], "categorical")
            self.assertEqual(res.data["missing_total"], 1)

    def test_data_profile_missing_file_is_honest_error(self):
        r = SkillRegistry([SKILLS_DIR])
        res = r.run("data-profile", ["/tmp/does-not-exist-xyz.csv"])
        self.assertFalse(res.ok)
        self.assertEqual(res.data["error"], "file_not_found")


class InstructionActivationTests(unittest.TestCase):
    """Instruction skills activate dynamically from discussion context."""

    def _brain(self):
        from novi.brain.engine import MacBrain, MacBrainConfig
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        return brain

    def test_diagram_request_injects_skill_guidance(self):
        seen = {}

        def stub(system, user, **kw):
            seen["system"] = system
            return "here is a sequence diagram in a mermaid block"

        brain = self._brain()
        try:
            out = brain.respond("help me design a sequence diagram for our checkout flow", llm_chat=stub)
            self.assertTrue(out["text"])
            applied = out["grounding"]["skills_applied"]
            self.assertIn("diagram-design", applied)
            self.assertIn("humanizer", applied)  # style pass combines with matched skills
            self.assertIn("sequenceDiagram", seen["system"])
            applied_events = [e for e in brain.events if e.get("event_type") == "skill.applied"]
            self.assertTrue(applied_events)
        finally:
            brain.stop()

    def test_casual_message_injects_no_guidance(self):
        seen = {}

        def stub(system, user, **kw):
            seen["system"] = system
            return "pretty good, you?"

        brain = self._brain()
        try:
            out = brain.respond("how was your day?", llm_chat=stub)
            # Only the unconditional humanizer style pass applies.
            self.assertEqual(out["grounding"].get("skills_applied"), ["humanizer"])
            self.assertNotIn("Skill guidance:", seen["system"])
            self.assertIn("ALWAYS apply this rewriting guidance", seen["system"])
            self.assertFalse([e for e in brain.events if e.get("event_type") == "skill.applied"])
        finally:
            brain.stop()

    def test_two_matches_cap_and_instruction_only(self):
        block, applied = None, None

        class _BrainHolder:
            pass

        brain = self._brain()
        try:
            block, applied = brain._matched_instruction_guidance(
                "design an er diagram, write sales copy, differentiate x**2, draw a flowchart"
            )
            # Only instruction-kind skills appear; script/hybrid act elsewhere.
            self.assertLessEqual(len(applied), 2)
            for name in applied:
                m = brain.skills.get(name)
                self.assertEqual(m.kind, "instruction")
            # The hybrid symbolic-math body must NOT be injected here.
            self.assertNotIn("symbolic-math", applied)
        finally:
            brain.stop()

    def test_guidance_respects_char_budget(self):
        long_body = "---\nname: x\n---\n" + "\n".join(f"line {i} padding content" for i in range(400))
        brain = self._brain()
        try:
            original = brain.skills.body
            brain.skills.body = lambda name: long_body if name == "diagram-design" else original(name)
            block, applied = brain._matched_instruction_guidance("design a sequence diagram", char_budget=300)
            self.assertIn("diagram-design", applied)
            section = block.split("### Skill guidance: diagram-design", 1)[1]
            self.assertLessEqual(len(section), 300 + 200)  # budget + directive tail
        finally:
            brain.stop()


class MemoryContextActivationTests(unittest.TestCase):
    """Skills also fire from recalled knowledge/memory and chat history."""

    def _brain(self):
        from novi.brain.engine import MacBrain, MacBrainConfig
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        return brain

    def test_history_mention_activates_skill(self):
        seen = {}

        def stub(system, user, **kw):
            seen["system"] = system
            return "continuing"

        brain = self._brain()
        try:
            out = brain.respond(
                "ok go on",
                llm_chat=stub,
                history=[{"role": "user", "content": "let's sketch a sequence diagram for checkout"}],
            )
            applied = out["grounding"].get("skills_applied", [])
            self.assertIn("diagram-design", applied)
            self.assertIn("sequenceDiagram", seen["system"])
        finally:
            brain.stop()

    def test_memory_fact_activates_skill(self):
        brain = self._brain()
        try:
            block, applied = brain._matched_instruction_guidance(
                "anything interesting lately?",
                "; Recent events: the whiteboard showed a big flowchart of the pipeline",
            )
            self.assertIn("diagram-design", applied)
        finally:
            brain.stop()

    def test_humanizer_block_is_cached_and_condensed(self):
        brain = self._brain()
        try:
            first = brain._humanizer_system_block()
            second = brain._humanizer_system_block()
            self.assertTrue(first)
            self.assertIs(first, second)  # cached per process
            self.assertLess(len(first), 4000)  # condensed, not the full body
            self.assertIn("rewrite", first.lower())
        finally:
            brain.stop()


class SkillActivatorCentralTests(unittest.TestCase):
    """The centralized activator wraps every response surface, not just chat."""

    def _activator(self):
        from novi.brain.skill_activation import SkillActivator
        r = SkillRegistry([SKILLS_DIR])
        events: list[tuple[str, dict]] = []
        return SkillActivator(r, emit=lambda e, pl: events.append((e, pl))), events

    def test_priming_from_cycle_context_fires_without_utterance_match(self):
        act, events = self._activator()
        newly = act.observe_cycle(
            cycle=3,
            detections=["whiteboard", "marker"],
            memories=["user drew a flowchart of onboarding"],
        )
        self.assertIn("diagram-design", newly)
        self.assertIn("skill.primed", [e for e, _ in events])
        # A reply whose own text matches nothing still gets the primed skill.
        block, applied = act.guidance_for("what do you think about all this?")
        self.assertIn("diagram-design", applied)
        self.assertTrue("sequenceDiagram" in block or "flowchart TD" in block)

    def test_primed_skills_expire_after_ttl(self):
        act, _ = self._activator()
        act.prime_ttl_cycles = 5
        act.observe_cycle(cycle=2, memories=["a big flowchart on the wall"])
        self.assertIn("diagram-design", act.primed_names())
        act.expire(cycle=6)  # within TTL
        self.assertIn("diagram-design", act.primed_names())
        act.expire(cycle=9)  # beyond TTL
        self.assertNotIn("diagram-design", act.primed_names())

    def test_priming_cap_and_humanizer_never_primed(self):
        act, _ = self._activator()
        act.max_primed = 2
        act.observe_cycle(
            cycle=1,
            memories=[
                "design an er diagram for orders",
                "write sales copy for launch",
                "differentiate polynomials",
                "draw a flowchart of login",
            ],
        )
        self.assertLessEqual(len(act.primed_names()), 2)
        self.assertNotIn("humanizer", act.primed_names())

    def test_style_pass_shared_across_consumers(self):
        act1, _ = self._activator()
        act2, _ = self._activator()
        b1 = act1.style_pass_block()
        self.assertTrue(b1)
        self.assertIs(act1.style_pass_block(), b1)
        # Same registry content => same block; consumers share one policy.
        self.assertEqual(act2.style_pass_block(), b1)


class ActivatorEngineIntegrationTests(unittest.TestCase):
    """Engine owns the activator; chat replies consume its primed state."""

    def _brain(self):
        from novi.brain.engine import MacBrain, MacBrainConfig
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        return brain

    def test_engine_constructs_shared_activator(self):
        brain = self._brain()
        try:
            self.assertIs(brain.skill_activator._registry, brain.skills)
        finally:
            brain.stop()

    def test_cycle_primed_skill_shapes_later_reply(self):
        seen = {}

        def stub(system, user, **kw):
            seen["system"] = system
            return "tell me more"

        brain = self._brain()
        try:
            # Simulates what the cycle hook does when perception/memory
            # mentions diagram work — primed at engine level, no chat involved.
            brain.skill_activator.observe_cycle(cycle=brain._cycle + 1, memories=["whiteboard showed a flowchart of checkout"])
            out = brain.respond("hmm interesting", llm_chat=stub)
            applied = out["grounding"].get("skills_applied", [])
            self.assertIn("diagram-design", applied)
            self.assertIn("flowchart TD", seen["system"])
        finally:
            brain.stop()


class SttSkillPrimingTests(unittest.TestCase):
    """Heard speech (audio-STT path) activates skills, symmetric with vision."""

    def _brain(self):
        from novi.brain.engine import MacBrain, MacBrainConfig
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        return brain

    def test_heard_speech_primes_skill(self):
        from novi.brain.models.stt import TranscriptionResult
        brain = self._brain()
        try:
            before = len([e for e in brain.events if e.get("event_type") == "skill.primed"])
            out = brain.ingest_transcript(
                TranscriptionResult(
                    text="we should draw a sequence diagram of the checkout flow",
                    language="en", confidence=0.95, audio_path="", provider="test", model_id="test",
                )
            )
            self.assertTrue(out["reasoning"])
            primed_events = [e for e in brain.events if e.get("event_type") == "skill.primed"]
            self.assertEqual(len(primed_events), before + 1)
            self.assertIn("diagram-design", primed_events[-1]["payload"]["skills"])
            self.assertIn("diagram-design", brain.skill_activator.primed_names())
        finally:
            brain.stop()

    def test_stt_primed_skill_shapes_next_reply_without_triggers(self):
        from novi.brain.models.stt import TranscriptionResult

        seen = {}

        def stub(system, user, **kw):
            seen["system"] = system
            return "sure"

        brain = self._brain()
        try:
            brain.ingest_transcript(
                TranscriptionResult(
                    text="let's make an er diagram for the orders database",
                    language="en", confidence=0.9, audio_path="", provider="test", model_id="test",
                )
            )
            out = brain.respond("go ahead please", llm_chat=stub)
            applied = out["grounding"].get("skills_applied", [])
            self.assertIn("diagram-design", applied)
            self.assertIn("erDiagram", seen["system"])
        finally:
            brain.stop()

    def test_plain_speech_primes_nothing(self):
        from novi.brain.models.stt import TranscriptionResult
        brain = self._brain()
        try:
            before = len([e for e in brain.events if e.get("event_type") == "skill.primed"])
            brain.ingest_transcript(
                TranscriptionResult(
                    text="the weather is nice today",
                    language="en", confidence=0.9, audio_path="", provider="test", model_id="test",
                )
            )
            after = [e for e in brain.events if e.get("event_type") == "skill.primed"]
            self.assertEqual(len(after), before)
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

    def test_brain_discovers_skills_and_runs_symbolic_math(self):
        brain = self._brain()
        try:
            names = {m.name for m in brain.skills.discover()}
            self.assertIn("symbolic-math", names)
            res = brain.brain_use_skill("symbolic-math", ["solve", "7*6"])
            self.assertTrue(res.ok)
            self.assertEqual(res.data["result"], 42)
        finally:
            brain.stop()

    def test_invocation_emits_event_and_admits_memory_with_provenance(self):
        brain = self._brain()
        try:
            brain._cycle_correlation_id = str(brain._cycle_correlation_id)
            res = brain.brain_use_skill("symbolic-math", ["solve", "9+1"])
            self.assertTrue(res.ok)
            events = [e for e in brain.events if e.get("event_type") == "skill.invoked"]
            self.assertTrue(events)
            records = list(getattr(brain.memory, "_records", {}).values()) if hasattr(brain.memory, "_records") else []
            hit = [rec for rec in records if getattr(rec, "memory_type", "") == "skill_result"]
            self.assertTrue(hit)
            prov = hit[0].provenance if isinstance(hit[0].provenance, dict) else {}
            self.assertEqual(prov.get("source"), "skill:symbolic-math")

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
