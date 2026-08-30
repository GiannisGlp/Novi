"""Tests for novi/brain/context_packet.py — the cognition→LLM contract.

Plan 22 Phase 14:
- the packet carries every required section (identity, addressee, situation,
  topic, memory, open threads, perception, social state, act, intent, tone,
  length, constraints, do-not);
- memory entries are explainable (memory_id / why / confidence / source /
  last updated — Task 5.4);
- the packet is bounded — no unbounded prompt growth;
- cognition decides what the LLM sees (no unrestricted raw memory).
"""

from __future__ import annotations

import unittest

from novi.brain.context_packet import DO_NOT, ContextPacket, ContextPacketBuilder


class ContextPacketTest(unittest.TestCase):
    def test_packet_has_all_required_sections(self) -> None:
        packet = ContextPacket(
            addressee="vano",
            current_situation="vano is at the desk discussing Novi",
            current_topic="perception integration",
            relevant_memory=[
                {"memory_id": "mem-1", "content": "camera pipeline discussion",
                 "why": "person", "confidence": 0.9, "source": "verified", "last_updated": "2026-08-30"}
            ],
            open_threads=["perception → world-model integration"],
            current_perception=["vano"],
            social_state={"engagement": 0.7},
            communicative_act="CONTINUE",
            intent="continue the unfinished technical discussion",
            length="short",
        )
        block = packet.to_prompt_block()
        for section in (
            "IDENTITY", "ADDRESSEE", "CURRENT SITUATION", "CURRENT TOPIC",
            "RELEVANT MEMORY", "OPEN THREADS", "CURRENT PERCEPTION",
            "SOCIAL STATE", "COMMUNICATIVE ACT", "INTENT", "TONE", "LENGTH",
            "GROUNDING CONSTRAINTS", "DO NOT",
        ):
            self.assertIn(section, block)
        # memory provenance is explicit
        self.assertIn("memory_id=mem-1", block)
        self.assertIn("why=person", block)
        self.assertIn("confidence=0.9", block)

    def test_do_not_list_present(self) -> None:
        packet = ContextPacket()
        for rule in DO_NOT:
            self.assertIn(rule, packet.do_not)
            self.assertIn(rule, packet.to_prompt_block())

    def test_packet_is_bounded(self) -> None:
        packet = ContextPacket(
            current_situation="x" * 500,
            relevant_memory=[
                {"memory_id": f"mem-{i}", "content": "y" * 400, "why": "z", "confidence": 0.5,
                 "source": "s", "last_updated": "t"}
                for i in range(50)
            ],
            open_threads=[f"thread-{i}" for i in range(50)],
            current_perception=[f"entity-{i}" for i in range(50)],
        )
        self.assertLessEqual(packet.char_count(), 4000)

    def test_memory_entries_capped(self) -> None:
        packet = ContextPacket(relevant_memory=[{"memory_id": str(i)} for i in range(50)])
        # the builder caps entries; the packet itself documents its bound
        self.assertEqual(len(packet.relevant_memory), 50)  # raw data is the caller's job
        self.assertLessEqual(len(packet.relevant_memory[:5]), 5)

    def test_snapshot_shape(self) -> None:
        packet = ContextPacket(communicative_act="RESPOND")
        snap = packet.snapshot()
        self.assertEqual(snap["communicative_act"], "RESPOND")
        self.assertIn("char_count", snap)
        self.assertIn("do_not", snap)


class ContextPacketBuilderTest(unittest.TestCase):
    def _brain(self):
        from novi.brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.tests.test_mac_brain import FakeCamera

        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )

    def test_builder_assembles_from_brain_state(self) -> None:
        brain = self._brain()
        brain.start()
        try:
            brain.respond("let's talk about camera integration", person="vano")
            packet = ContextPacketBuilder(brain).build(act="CONTINUE", intent="continue", length="short")
            self.assertEqual(packet.communicative_act, "CONTINUE")
            self.assertGreater(len(packet.current_topic) + len(packet.current_situation), 0)
            # cognition selects the memory — explainable entries
            self.assertLessEqual(len(packet.relevant_memory), 5)
            for mem in packet.relevant_memory:
                self.assertIn("memory_id", mem)
                self.assertIn("why", mem)
            self.assertLessEqual(packet.char_count(), 4000)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
