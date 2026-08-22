"""Cognition 2.0: richer situation understanding + memory-grounded reasoning.

Verifies that MacCognition grounds its reasoning in knowledge-graph relations,
active-goal context, and recalled memories, and produces multiple hypotheses
plus temporal/causal inferences.
"""

import unittest

from brain.b1_cognition import SensorObservation
from brain.b1_world import WorldEntityState, WorldModelState
from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from MAC_BRAIN.autonomy import Goal
from MAC_BRAIN.cognition2 import MacCognition
from MAC_BRAIN.models.stt import TranscriptionResult
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


def _state() -> WorldModelState:
    return WorldModelState(
        entities={
            "door": WorldEntityState("door", "hallway", "open", 0.9, 1),
            "alice": WorldEntityState("alice", "hallway", "present", 0.9, 1),
        }
    )


def _obs(entity: str = "door") -> tuple[SensorObservation, ...]:
    return (SensorObservation(1, "cam.perception", entity, None, "open", 0.9, 1),)


class MacCognitionTests(unittest.TestCase):
    def test_situation_carries_relations_goal_recalled(self):
        c = MacCognition()
        knowledge = [{"subject": "alice", "predicate": "moved", "object": "door", "confidence": 0.8, "status": "active"}]
        goal = {"kind": "reach", "target": [3, 0], "distance_to_goal": 1.0}
        recalled = ({"memory_type": "utterance", "content": "alice moved the door"},)
        cs = c.cycle(_state(), _obs(), cycle=1, knowledge=knowledge, goal=goal, recalled=recalled)
        self.assertTrue(cs.situation.relations)
        self.assertEqual(cs.situation.goal, goal)
        self.assertEqual(len(cs.situation.recalled), 1)

    def test_causal_inference_from_knowledge(self):
        c = MacCognition()
        knowledge = [{"subject": "alice", "predicate": "moved", "object": "door", "confidence": 0.8, "status": "active"}]
        cs = c.cycle(_state(), _obs(), cycle=1, knowledge=knowledge, goal=None, recalled=())
        self.assertIn("alice likely moved door", cs.reasoning.inferences)
        self.assertEqual(cs.reasoning.conclusion, "causal_change_inferred")
        self.assertTrue(cs.reasoning.hypotheses)

    def test_goal_relevance_when_near_target(self):
        c = MacCognition()
        goal = {"kind": "reach", "target": [0, 0], "distance_to_goal": 0.4}
        cs = c.cycle(_state(), _obs(), cycle=1, knowledge=(), goal=goal, recalled=())
        self.assertEqual(cs.reasoning.conclusion, "goal_relevant_change")
        self.assertIn("goal target reached", cs.reasoning.inferences)

    def test_base_behavior_preserved(self):
        c = MacCognition()
        cs = c.cycle(_state(), _obs(), cycle=1, knowledge=(), goal=None, recalled=())
        # no knowledge/goal -> falls back to a base salience conclusion
        self.assertIn(cs.reasoning.conclusion, {
            "human_speech_observed",
            "person_alice_is_relevant_to_current_situation",
            "environmental_change_is_relevant",
            "no_high_salience_change_detected",
        })


class AliceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.9, (0.0, 0.0, 1.0, 1.0)),)


class CognitionRuntimeIntegrationTests(unittest.TestCase):
    def _brain(self):
        return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(AliceBackend()), config=MacBrainConfig())

    def test_step_grounds_cognition_in_knowledge_and_goal(self):
        brain = self._brain()
        brain.start()
        try:
            brain.ingest_transcript(TranscriptionResult(text="alice moved the door", language="en", confidence=0.9, audio_path="", provider="web", model_id="web"))
            brain.set_goal(Goal.reach(3.0, 0.0, max_steps=60))
            brain.step()
            trace = brain._last_reasoning_trace
            # Cognition 2.0 fields are present in the trace
            self.assertIn("inferences", trace)
            self.assertIn("hypotheses", trace)
            self.assertIn("situation", trace)
            # the knowledge triple is surfaced as a relation and drives a causal inference
            relations = (trace.get("situation") or {}).get("relations") or []
            self.assertTrue(any(r.get("subject") == "alice" and r.get("predicate") == "moved" for r in relations), relations)
            self.assertTrue(any("alice likely moved door" in i for i in trace["inferences"]), trace["inferences"])
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
