"""Phase C2 (gap-audit plan 13): memory classes enforced at admission.

Pins:
  - classify_memory routes engine memory_types to canonical classes
    (EPISODIC for utterance/audio_event/perception/goal_outcome; SEMANTIC for
    knowledge/fact/summary; safe EPISODIC default);
  - MemoryClassDecisionRegistry.gate() admits implemented classes and refuses
    deferred ones with the recorded rationale state;
  - engine admissions stamp provenance["memory_class"] on every record;
  - a deferring registry blocks admission and emits memory.class_deferred.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.memory_classes import (
    DEFERRED_CLASSES,
    IMPLEMENTED_NOW,
    MemoryClass,
    MemoryClassDecisionRegistry,
    classify_memory,
)
from novi.brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain() -> MacBrain:
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(CupBackend()),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    return brain


def _all_records(brain: MacBrain) -> list:
    """Records across both store backends (durable rows vs in-memory dict)."""
    mem = brain.memory
    if hasattr(mem, "active_rows"):
        return [item["record"] for item in mem.active_rows()]
    return list(getattr(mem, "_records", {}).values())


class ClassifyMemoryTests(unittest.TestCase):
    def test_engine_types_map_to_episodic(self):
        for mt in ("utterance", "audio_event", "perception", "goal_outcome"):
            self.assertEqual(classify_memory(mt), MemoryClass.EPISODIC, mt)

    def test_knowledge_types_map_to_semantic(self):
        for mt in ("knowledge", "fact", "summary", "triple"):
            self.assertEqual(classify_memory(mt), MemoryClass.SEMANTIC, mt)

    def test_candidate_and_unknown_fallback(self):
        self.assertEqual(classify_memory("routine"), MemoryClass.ROUTINE_CANDIDATE)
        self.assertEqual(classify_memory("daily_procedural_candidate"), MemoryClass.PROCEDURAL_CANDIDATE)
        self.assertEqual(classify_memory("mystery_stream"), MemoryClass.EPISODIC)
        self.assertEqual(classify_memory("prospective"), MemoryClass.PROSPECTIVE)


class RegistryGateTests(unittest.TestCase):
    def test_implemented_classes_pass_the_gate(self):
        reg = MemoryClassDecisionRegistry()
        allowed, cls, state = reg.gate("utterance")
        self.assertTrue(allowed)
        self.assertEqual(cls, "episodic")
        self.assertEqual(state, "implemented")

    def test_deferred_classes_are_refused(self):
        reg = MemoryClassDecisionRegistry()
        for mt in ("procedural_competence", "prospective", "metamemory", "autobiographical"):
            allowed, cls, state = reg.gate(mt)
            self.assertFalse(allowed, mt)
            self.assertEqual(state, "deferred")
        self.assertTrue(DEFERRED_CLASSES.isdisjoint(IMPLEMENTED_NOW))


class EngineAdmissionStampTests(unittest.TestCase):
    def test_perception_admissions_carry_memory_class(self):
        brain = _brain()
        try:
            brain.step()
            records = _all_records(brain)
            classes = [r.provenance.get("memory_class") for r in records]
            self.assertIn("episodic", classes)
        finally:
            brain.stop()

    def test_utterance_admission_carries_memory_class(self):
        brain = _brain()
        try:

            class T:
                text = "hello there friend"
                confidence = 0.9
                provider = "test"
                model_id = "m"
                audio_path = ""

            brain.ingest_transcript(T())
            utt = [r for r in _all_records(brain) if r.memory_type == "utterance"]
            self.assertTrue(utt)
            self.assertEqual(utt[-1].provenance.get("memory_class"), "episodic")
        finally:
            brain.stop()

    def test_deferring_registry_blocks_admission_and_emits_event(self):
        class DeferringRegistry(MemoryClassDecisionRegistry):
            def gate(self, memory_type):
                return (False, classify_memory(memory_type).value, "deferred")

        brain = _brain()
        try:
            brain.memory_classes = DeferringRegistry()
            before = len(_all_records(brain))
            brain.step()
            events = [e["event_type"] for e in brain.events]
            self.assertIn("memory.class_deferred", events)

            class T:
                text = "should not be stored"
                confidence = 0.9
                provider = "test"
                model_id = "m"
                audio_path = ""

            brain.ingest_transcript(T())
            records = _all_records(brain)
            after_types = {r.memory_type for r in records}
            self.assertNotIn("utterance", after_types)
            self.assertLessEqual(len(records), before + 1)  # perception also gated
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
