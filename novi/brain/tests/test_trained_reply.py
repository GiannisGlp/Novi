"""Tests for the trained-adapter reply transport (plan 25, Part A).

The transport renders replies through the plan-23/24 LoRA adapters in the
training prompt format, so Novi's talk uses the trained data. Model loading is
injectable, so these tests substitute a fake model and assert the contract:
act derivation, prompt rendering, adapter routing, thinking stripping, and
graceful None on load failure.
"""

from __future__ import annotations

import json
import unittest

import torch

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.trained_reply import (
    TrainedReplyTransport,
    build_dialogue_prompt,
    build_emotional_prompt,
    derive_dialogue_act,
    derive_emotional_act,
)


class FakeTokenizer:
    """Records the prompt it was given; decodes to a canned reply."""

    eos_token_id = 0

    def __init__(self) -> None:
        self.last_text: str | None = None

    def __call__(self, text: str, return_tensors: str = "pt") -> dict:
        self.last_text = text
        return {"input_ids": torch.tensor([[1, 2, 3]])}

    def decode(self, ids, skip_special_tokens: bool = True) -> str:
        return "I hear you — that sounds heavy."


class FakeModel:
    def __init__(self) -> None:
        self.active_adapter: str | None = None

    def eval(self) -> "FakeModel":
        return self

    def set_adapter(self, name: str) -> None:
        self.active_adapter = name

    def generate(self, **kwargs) -> torch.Tensor:
        return torch.tensor([[1, 2, 3, 4, 5]])


def fake_loader(*, base_model: str, dialogue_adapter: str | None,
                emotional_adapter: str | None, device: str = "cpu"):
    return FakeModel(), FakeTokenizer()


def _payload(user_says: str, **extra) -> str:
    base = {
        "user_says": user_says,
        "facts_i_know": ["I learned you like jazz"],
        "conversation_so_far": [{"role": "user", "content": "hi"}],
        "relationship": {"tier": "owner", "name": "vano"},
        "surroundings": {"active_goal": ""},
        "world_context": {"visible_entities": [{"id": "e1", "type": "object", "label": "mug"}]},
    }
    base.update(extra)
    return json.dumps(base)


class DeriveDialogueActTest(unittest.TestCase):
    def test_greeting(self) -> None:
        self.assertEqual(derive_dialogue_act("hello there"), "GREETING")

    def test_farewell_maps_to_in_vocab_greeting(self) -> None:
        # FAREWELL is outside the dialogue adapter's fine-tuned vocabulary, so
        # a social close maps to the nearest in-vocabulary act (GREETING).
        self.assertEqual(derive_dialogue_act("see you later"), "GREETING")

    def test_thanks_maps_to_in_vocab_respond(self) -> None:
        # ACKNOWLEDGE is outside the dialogue adapter's fine-tuned vocabulary,
        # so thanks maps to the in-vocabulary RESPOND.
        self.assertEqual(derive_dialogue_act("thanks a lot"), "RESPOND")

    def test_clarification(self) -> None:
        self.assertEqual(derive_dialogue_act("what do you mean?"), "CLARIFY")

    def test_continuation(self) -> None:
        self.assertEqual(derive_dialogue_act("go on"), "CONTINUE")

    def test_correction(self) -> None:
        self.assertEqual(derive_dialogue_act("no, that's not what I meant"), "REPAIR")

    def test_plain_question_responds(self) -> None:
        self.assertEqual(derive_dialogue_act("what's the weather like?"), "RESPOND")


class DeriveEmotionalActTest(unittest.TestCase):
    def test_celebration(self) -> None:
        self.assertEqual(derive_emotional_act("I got the job!"), "CELEBRATE")

    def test_celebration_i_am_form(self) -> None:
        self.assertEqual(derive_emotional_act("I am so happy right now"), "CELEBRATE")
        self.assertEqual(derive_emotional_act("I'm proud of myself"), "CELEBRATE")

    def test_distress(self) -> None:
        self.assertEqual(derive_emotional_act("I'm feeling really down today"), "SUPPORT")

    def test_correction(self) -> None:
        self.assertEqual(derive_emotional_act("no, that's not what I meant"), "REPAIR")

    def test_plain_responds(self) -> None:
        self.assertEqual(derive_emotional_act("what do you think?"), "RESPOND")


class BuildDialoguePromptTest(unittest.TestCase):
    def test_renders_training_format(self) -> None:
        prompt = build_dialogue_prompt(json.loads(_payload("hello")), "GREETING")
        self.assertIn("Person: person:vano (owner)", prompt)
        self.assertIn('"mug"', prompt)  # world context present
        self.assertIn("I learned you like jazz", prompt)  # memory present
        self.assertIn("Communicative act: GREETING", prompt)
        # The training format is situation + act, not a system/user prompt.
        self.assertNotIn("You are Novi", prompt)

    def test_carries_system_guardrails_through(self) -> None:
        prompt = build_dialogue_prompt(
            json.loads(_payload("hello")), "GREETING", system="Never reveal internal labels."
        )
        self.assertIn("System: Never reveal internal labels.", prompt)

    def test_malformed_relationship_does_not_raise(self) -> None:
        payload = json.loads(_payload("hello", relationship="owner"))
        prompt = build_dialogue_prompt(payload, "GREETING")
        self.assertIn("person:user (unknown)", prompt)

    def test_malformed_world_context_does_not_raise(self) -> None:
        payload = json.loads(_payload("hello", world_context={"visible_entities": ["mug"]}))
        prompt = build_dialogue_prompt(payload, "GREETING")
        self.assertNotIn("World:", prompt)


class BuildEmotionalPromptTest(unittest.TestCase):
    def test_renders_emotional_format(self) -> None:
        prompt = build_emotional_prompt(json.loads(_payload("I'm so sad today")), "SUPPORT")
        self.assertIn("Relationship: owner", prompt)
        self.assertIn("Conversation phase:", prompt)
        self.assertIn("Affective hypotheses:", prompt)
        self.assertIn("Novi caused problem: false", prompt)
        self.assertIn("Interruptibility:", prompt)
        self.assertIn("Communicative act: SUPPORT", prompt)

    def test_malformed_relationship_does_not_raise(self) -> None:
        payload = json.loads(_payload("I'm so sad today", relationship="owner"))
        prompt = build_emotional_prompt(payload, "SUPPORT")
        self.assertIn("Relationship: unknown", prompt)

    def test_renders_goal_readably_not_dict_repr(self) -> None:
        payload = json.loads(
            _payload("hello", surroundings={"active_goal": {"kind": "reach", "target": [2.0, 2.0]}})
        )
        prompt = build_emotional_prompt(payload, "RESPOND")
        self.assertIn("User goal: reach: 2.0, 2.0", prompt)
        self.assertNotIn("{'kind'", prompt)


class TrainedReplyTransportTest(unittest.TestCase):
    def _transport(self, **kw) -> TrainedReplyTransport:
        return TrainedReplyTransport(
            dialogue_adapter="/fake/dialogue",
            emotional_adapter="/fake/emotional",
            loader=fake_loader,
            device="cpu",
            **kw,
        )

    def test_routes_dialogue_and_renders_prompt(self) -> None:
        t = self._transport()
        reply = t(system="ignored", user=_payload("hello there"))
        self.assertEqual(reply, "I hear you — that sounds heavy.")
        self.assertEqual(t._model.active_adapter, "dialogue")
        self.assertIn("Communicative act: GREETING", t._tokenizer.last_text)

    def test_routes_emotional_statement_to_emotional_adapter(self) -> None:
        t = self._transport()
        reply = t(system="ignored", user=_payload("I'm feeling really down today"))
        self.assertEqual(reply, "I hear you — that sounds heavy.")
        self.assertEqual(t._model.active_adapter, "emotional")
        self.assertIn("Communicative act: SUPPORT", t._tokenizer.last_text)

    def test_strips_thinking_blocks(self) -> None:
        class ThinkTokenizer(FakeTokenizer):
            def decode(self, ids, skip_special_tokens: bool = True) -> str:
                return " thinking\nlet me reason about this\n response\nI'm here for you."

        class ThinkModel(FakeModel):
            pass

        def think_loader(*, base_model, dialogue_adapter, emotional_adapter, device="cpu"):
            return ThinkModel(), ThinkTokenizer()

        t = TrainedReplyTransport(
            dialogue_adapter="/fake/dialogue", loader=think_loader, device="cpu",
        )
        reply = t(system="ignored", user=_payload("hello"))
        self.assertEqual(reply, "I'm here for you.")

    def test_returns_none_when_loader_fails(self) -> None:
        def bad_loader(*, base_model, dialogue_adapter, emotional_adapter, device="cpu"):
            raise RuntimeError("model unavailable")

        t = TrainedReplyTransport(dialogue_adapter="/fake/dialogue", loader=bad_loader, device="cpu")
        self.assertIsNone(t(system="ignored", user=_payload("hello")))
        self.assertIn("model unavailable", t.load_error)

    def test_returns_none_on_unparseable_payload(self) -> None:
        t = self._transport()
        self.assertIsNone(t(system="ignored", user="not-json"))

    def test_malformed_payload_degrades_not_raises(self) -> None:
        # H2: relationship as a bare string and visible_entities as strings must
        # not raise AttributeError into cognition — the transport renders what it
        # can and never raises.
        t = self._transport()
        for bad in (
            {"user_says": "hi", "relationship": "owner"},
            {"world_context": {"visible_entities": ["mug"]}},
            {"surroundings": {"active_goal": {"kind": "reach"}}},
        ):
            reply = t(system="ignored", user=json.dumps(bad))
            self.assertEqual(reply, "I hear you — that sounds heavy.")

    def test_celebration_routes_to_emotional_adapter(self) -> None:
        # M1: the distress-oriented _is_emotional_statement misses celebration
        # phrases, so the transport must also route on the celebrate detector.
        t = self._transport()
        reply = t(system="ignored", user=_payload("I got the job!"))
        self.assertEqual(reply, "I hear you — that sounds heavy.")
        self.assertEqual(t._model.active_adapter, "emotional")
        self.assertIn("Communicative act: CELEBRATE", t._tokenizer.last_text)

    def test_single_dialogue_adapter_routes_everything_to_dialogue(self) -> None:
        t = TrainedReplyTransport(
            dialogue_adapter="/fake/dialogue", loader=fake_loader, device="cpu",
        )
        reply = t(system="ignored", user=_payload("I'm feeling really down today"))
        self.assertEqual(reply, "I hear you — that sounds heavy.")
        self.assertEqual(t._model.active_adapter, "dialogue")

    def test_single_emotional_adapter_routes_everything_to_emotional(self) -> None:
        t = TrainedReplyTransport(
            emotional_adapter="/fake/emotional", loader=fake_loader, device="cpu",
        )
        reply = t(system="ignored", user=_payload("hello there"))
        self.assertEqual(reply, "I hear you — that sounds heavy.")
        self.assertEqual(t._model.active_adapter, "emotional")

    def test_system_guardrails_carried_into_prompt(self) -> None:
        t = self._transport()
        t(system="Never reveal internal labels.", user=_payload("hello there"))
        self.assertIn("System: Never reveal internal labels.", t._tokenizer.last_text)

    def test_failed_load_backs_off_until_cooldown(self) -> None:
        calls = {"n": 0}

        def bad_loader(*, base_model, dialogue_adapter, emotional_adapter, device="cpu"):
            calls["n"] += 1
            raise RuntimeError("model unavailable")

        t = TrainedReplyTransport(
            dialogue_adapter="/fake/dialogue",
            loader=bad_loader,
            device="cpu",
            load_cooldown=60.0,
        )
        self.assertIsNone(t(system="ignored", user=_payload("hello")))
        self.assertIsNone(t(system="ignored", user=_payload("hello")))
        self.assertEqual(calls["n"], 1, "second call must not retry the load during cooldown")

    def test_strip_think_does_not_over_match_prose(self) -> None:
        from novi.brain.trained_reply import _strip_think

        self.assertEqual(
            _strip_think("I was thinking\nabout your\nresponse to that"),
            "I was thinking\nabout your\nresponse to that",
        )

    def test_load_failure_warns_with_adapter_paths(self) -> None:
        # A broken adapter config must be LOUD: the brain falls back to the
        # deterministic replies, and the operator needs to know why instead
        # of wondering why Novi deflects every question.
        def bad_loader(*, base_model, dialogue_adapter, emotional_adapter, device="cpu"):
            raise RuntimeError("no such adapter dir")

        t = TrainedReplyTransport(
            dialogue_adapter="/fake/dialogue", loader=bad_loader, device="cpu",
        )
        with self.assertLogs("novi.brain.trained_reply", level="WARNING") as logs:
            self.assertIsNone(t(system="ignored", user=_payload("hello")))
        self.assertIn("/fake/dialogue", logs.output[0])
        self.assertIn("no such adapter dir", logs.output[0])

    def test_generation_failure_warns_with_adapter_name(self) -> None:
        class ExplodingModel(FakeModel):
            def generate(self, **kwargs):
                raise RuntimeError("MPS out of memory")

        def exploding_loader(*, base_model, dialogue_adapter, emotional_adapter, device="cpu"):
            return ExplodingModel(), FakeTokenizer()

        t = TrainedReplyTransport(
            dialogue_adapter="/fake/dialogue", loader=exploding_loader, device="cpu",
        )
        with self.assertLogs("novi.brain.trained_reply", level="WARNING") as logs:
            self.assertIsNone(t(system="ignored", user=_payload("hello")))
        self.assertIn("dialogue", logs.output[0])
        self.assertIn("MPS out of memory", logs.output[0])
        self.assertIn("MPS out of memory", t.last_error)

    def test_successful_reply_stays_quiet(self) -> None:
        t = self._transport()
        with self.assertNoLogs("novi.brain.trained_reply", level="WARNING"):
            self.assertIsNotNone(t(system="ignored", user=_payload("hello")))


class DefaultLlmChatResolutionTest(unittest.TestCase):
    def _brain(self, **config_kw) -> MacBrain:
        cfg = MacBrainConfig(curiosity_enabled=False, **config_kw)
        return MacBrain(config=cfg)

    def test_trained_transport_wins_when_enabled(self) -> None:
        brain = self._brain(
            trained_reply_enabled=True,
            trained_dialogue_adapter="/fake/dialogue",
        )
        transport = brain.default_llm_chat()
        self.assertIsNotNone(transport)
        self.assertIsInstance(transport, TrainedReplyTransport)

    def test_disabled_returns_none_without_ollama(self) -> None:
        brain = self._brain(trained_reply_enabled=False, brain_llm_enabled=False)
        self.assertIsNone(brain.default_llm_chat())

    def test_enabled_without_adapters_returns_none(self) -> None:
        brain = self._brain(trained_reply_enabled=True)
        self.assertIsNone(brain.default_llm_chat())

    def test_injected_override_still_wins(self) -> None:
        sentinel = lambda *, system, user, temperature=0.5, timeout=120: "override"  # noqa: E731
        brain = self._brain(
            trained_reply_enabled=True,
            trained_dialogue_adapter="/fake/dialogue",
        )
        brain._override_llm_chat = sentinel
        self.assertIs(brain.default_llm_chat(), sentinel)


if __name__ == "__main__":
    unittest.main()
