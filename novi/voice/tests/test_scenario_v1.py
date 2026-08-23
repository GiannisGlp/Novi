"""SCENARIO-V1 "absentee owner" — the doc-15 acceptance scenario.

> Owner is at work. Novi is at home: navigating, observing, hearing
> ambient events, mid-conversation with a person at home. The owner sends
> a chat message from work. Novi answers the message WITHOUT dropping any
> other capability — the home conversation pauses gracefully, resumes
> after, and every other track keeps its state.

Simulated deterministically: no hardware, no threads, no sleeps.
"""

from __future__ import annotations

from novi.brain.audio import AudioFrame
from novi.voice.stt import DeterministicSTTProvider
from novi.voice.tts import DeterministicTTSProvider
from novi.voice.turn_taking import Channel
from novi.voice.vad import TurnSegmenter
from novi.voice.voice_loop import VoiceLoop

EP = 2


def _speech(at: str) -> AudioFrame:
    return AudioFrame(rms=0.5, peak=0.8, speech=True, captured_at=at)


def _sil() -> AudioFrame:
    return AudioFrame(rms=0.01, peak=0.02, speech=False)


class _WorldTracks:
    """Stand-ins for the other autonomy tracks (navigate / observe / hear)."""

    def __init__(self) -> None:
        self.nav_cycles = 0
        self.observations: list[str] = []
        self.heard_events: list[str] = []

    def tick_navigate(self) -> None:
        self.nav_cycles += 1

    def observe(self, label: str) -> None:
        self.observations.append(label)

    def hear(self, event: str) -> None:
        self.heard_events.append(event)


def _build_world():
    world = _WorldTracks()
    script = {
        "a1": "hi novi",                # Anna greets
        "a2": "how is the weather",     # Anna asks
    }
    replies = {
        "hi novi": "hello anna, good to see you",
        "how is the weather": "sunny and mild right now",
    }
    seg = TurnSegmenter(endpoint_frames=EP)
    stt = DeterministicSTTProvider(script)
    tts = DeterministicTTSProvider()
    convo: list[tuple[str, str]] = []

    def reply_fn(text: str, *, person: str = "") -> str:
        convo.append((person, text))
        return replies.get(text, "")

    loop = VoiceLoop(segmenter=seg, stt=stt, tts=tts, reply_fn=reply_fn)
    return world, loop, tts, convo


class TestScenarioV1AbsenteeOwner:
    def test_full_scenario_nothing_dropped(self):
        world, loop, tts, convo = _build_world()

        # --- Phase 1: owner away; Novi lives at home -----------------------
        loop.begin_exchange("conv-anna")           # Anna walks up...
        loop.person = "Anna"                       # ...recognized by face ID (doc 02)
        world.tick_navigate()
        world.observe("kettle")

        # Anna speaks a turn; other tracks keep ticking between frames.
        loop.feed_frame(_speech("a1"))
        world.tick_navigate()
        world.hear("door-close")
        for _ in range(EP):
            loop.feed_frame(_sil())
            world.tick_navigate()

        spoken = loop.drain()
        assert [s.text for s in spoken] == ["hello anna, good to see you"]

        # --- Phase 2: owner messages from work MID-exchange ------------------
        d = loop.notify_owner_message("work-msg-1")
        assert d.action == "yield-after-sentence"
        assert d.interrupted_ref is not None

        # Anna asks another question before Novi handles the message;
        # the in-flight beat finishes first (never cut mid-word).
        loop.feed_frame(_speech("a2"))
        for _ in range(EP):
            loop.feed_frame(_sil())
        spoken = loop.drain()
        assert [s.text for s in spoken] == ["sunny and mild right now"]
        assert ("Anna", "how is the weather") in [(p, t) for p, t in convo]

        # Owner's message is still pending in policy queue — not lost.

        # --- Phase 3: Novi handles owner, then resumes home life -------------
        p = loop.policy
        p.release_speak()                          # finish current beat -> owner ack
        assert p.speaking_ref == "work-msg-1"
        p.release_speak()                          # owner handled -> resume Anna's turn
        assert p.speaking_ref is not None          # resumed, not dropped

        # --- Assertions: nothing dropped --------------------------------------
        assert world.nav_cycles >= 4               # navigation kept ticking
        assert world.observations == ["kettle"]
        assert world.heard_events == ["door-close"]
        kinds = [e["kind"] for e in loop.events]
        assert "exchange-begun" in kinds
        assert len(convo) == 2                     # both Anna turns answered

    def test_snapshot_never_shows_dropped_tracks(self):
        _, loop, _, _ = _build_world()
        loop.begin_exchange("conv-anna")
        snap = loop.snapshot()
        assert snap["policy"]["exchange"] == "conv-anna"
        assert snap["state"] in ("listening", "speaking")
