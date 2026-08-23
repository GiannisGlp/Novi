"""Tests: autonomy-owned turn-taking policy (doc 15).

Rules under test:
- one outbound voice lease at a time;
- higher-priority inbound never cuts mid-word -> yield-after-sentence,
  prior track recorded for explicit resume;
- queue drains by (priority desc, arrival asc);
- when queue empties, an interrupted track resumes before idle;
- every decision carries provenance.
"""

from __future__ import annotations

from novi.voice.turn_taking import Channel, TurnTakingPolicy


class TestLeaseBasics:
    def test_idle_request_granted_immediately(self):
        p = TurnTakingPolicy()
        d = p.request_speak(Channel.PERSON_VOICE, ref="greet-anna")
        assert d.granted is True
        assert d.reason == "lease-acquired"
        assert p.speaking_ref == "greet-anna"

    def test_second_request_while_leased_is_queued(self):
        p = TurnTakingPolicy()
        p.request_speak(Channel.PERSON_VOICE, ref="a")
        d = p.request_speak(Channel.PERSON_VOICE, ref="b")
        assert d.granted is False
        assert d.reason == "queued"
        assert p.speaking_ref == "a"

    def test_release_grants_next_queued_fifo_same_priority(self):
        p = TurnTakingPolicy()
        p.request_speak(Channel.PERSON_VOICE, ref="a")
        p.request_speak(Channel.PERSON_VOICE, ref="b")
        p.request_speak(Channel.PERSON_VOICE, ref="c")
        r1 = p.release_speak()
        assert r1.granted and p.speaking_ref == "b"
        r2 = p.release_speak()
        assert r2.granted and p.speaking_ref == "c"
        r3 = p.release_speak()
        assert r3.granted is False
        assert p.speaking_ref is None


class TestPriorityOrdering:
    def test_higher_priority_jumps_queue(self):
        p = TurnTakingPolicy()
        p.request_speak(Channel.AMBIENT, ref="musing")
        p.request_speak(Channel.OWNER_CHAT, ref="owner-answer")
        p.request_speak(Channel.SYSTEM, ref="status")
        order = ["musing"]
        while p.queue_depth:
            p.release_speak()
            if p.speaking_ref is not None:
                order.append(p.speaking_ref)
        assert order[0] == "musing"  # already holding lease
        assert order.index("owner-answer") < order.index("status")

    def test_owner_chat_beats_system_announcement(self):
        p = TurnTakingPolicy()
        p.request_speak(Channel.OWNER_CHAT, ref="answer-owner")
        p.request_speak(Channel.SYSTEM, ref="battery-low")
        assert p.speaking_ref == "answer-owner"
        p.release_speak()
        # system announcement auto-granted after owner handled
        assert p.speaking_ref == "battery-low"


class TestInterruptionAndResume:
    def test_higher_priority_inbound_yields_after_sentence_not_immediately(self):
        p = TurnTakingPolicy()
        p.begin_exchange(Channel.PERSON_VOICE, ref="conv-anna")
        p.request_speak(Channel.PERSON_VOICE, ref="sentence-to-anna")
        d = p.notify_inbound(Channel.OWNER_CHAT, ref="msg-from-work")
        assert d.action == "yield-after-sentence"
        assert d.interrupted_ref == "sentence-to-anna"
        assert p.speaking_ref == "sentence-to-anna", "mid-word cutoff forbidden"

    def test_resume_recorded_and_replayed_when_queue_drains(self):
        p = TurnTakingPolicy()
        p.begin_exchange(Channel.PERSON_VOICE, ref="conv-anna")
        p.request_speak(Channel.PERSON_VOICE, ref="to-anna")
        p.notify_inbound(Channel.OWNER_CHAT, ref="work-msg")
        p.release_speak()  # finish sentence -> owner ack granted
        assert p.speaking_ref == "work-msg"
        p.release_speak()  # owner handled, queue empty -> resume anna's turn
        assert p.speaking_ref == "to-anna"

    def test_lower_priority_inbound_while_speaking_does_not_yield(self):
        p = TurnTakingPolicy()
        p.begin_exchange(Channel.OWNER_CHAT, ref="owner-talk")
        p.request_speak(Channel.OWNER_CHAT, ref="talking-to-owner")
        d = p.notify_inbound(Channel.AMBIENT, ref="door-sound")
        assert d.action == "queue-only"
        assert p.speaking_ref == "talking-to-owner"


class TestProvenance:
    def test_every_decision_logged(self):
        p = TurnTakingPolicy()
        p.request_speak(Channel.PERSON_VOICE, ref="x")
        p.notify_inbound(Channel.OWNER_CHAT, ref="y")
        p.release_speak()
        kinds = [e["kind"] for e in p.event_log]
        assert "speak-granted" in kinds
        assert "inbound-yield" in kinds
        assert "release-resume" in kinds or "release-next" in kinds or "release-idle" in kinds
        for e in p.event_log:
            assert "reason" in e and "at_cycle" in e

    def test_snapshot_for_web_observers(self):
        p = TurnTakingPolicy()
        p.begin_exchange(Channel.PERSON_VOICE, ref="c1")
        snap = p.snapshot()
        assert snap["state"] in ("listening", "speaking")
        assert snap["exchange"] == "c1"
