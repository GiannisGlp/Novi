"""Autonomy-owned turn-taking policy.

Doc 15 authority decision: dialogue decides WHAT to say; this policy
decides WHEN Novi speaks/listens/yields. One outbound voice lease at a
time, priority arbitration between channels (person present, owner chat,
ambient, system), yield-after-sentence interruption semantics (never cut
mid-word), and explicit resume of interrupted exchanges.

Every decision is provenance-logged for the audit trail.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Channel(str, enum.Enum):
    """Communication channels competing for Novi's voice."""

    PERSON_VOICE = "person_voice"  # a physically-present person (highest social)
    OWNER_CHAT = "owner_chat"      # owner direct message from afar
    AMBIENT = "ambient"            # background/social listening commentary
    SYSTEM = "system"              # diagnostics/status announcements (lowest)


# Lower int = higher priority.
_PRIORITY: dict[Channel, int] = {
    Channel.PERSON_VOICE: 0,
    Channel.OWNER_CHAT: 0,
    Channel.AMBIENT: 2,
    Channel.SYSTEM: 3,
}


def _prio(ch: Channel) -> int:
    return _PRIORITY[ch]


@dataclass
class TurnDecision:
    """Outcome of a turn-taking request or inbound notification."""

    action: str            # granted | queued | yield-after-sentence | queue-only | released | resumed | idle
    granted: bool = False
    reason: str = ""
    channel: Channel | None = None
    ref: str = ""
    interrupted_ref: str | None = None

    def snapshot(self) -> dict:
        return {
            "action": self.action,
            "granted": self.granted,
            "reason": self.reason,
            "channel": self.channel.value if self.channel else None,
            "ref": self.ref,
        }


@dataclass
class _Entry:
    channel: Channel
    ref: str
    seq: int


class TurnTakingPolicy:
    """Speaking lease + priority queue + interrupt/resume bookkeeping.

    Deterministic: no clocks — cycle numbers are supplied by the caller so
    CI can replay exact interleavings of SCENARIO-V1.
    """

    def __init__(self) -> None:
        self._cycle = 0
        self._lease: _Entry | None = None          # current outbound utterance owner
        self._queue: list[_Entry] = []             # pending outbound utterances
        self._seq = 0
        self._interrupted: list[_Entry] = []       # LIFO resume stack
        self._event_log: list[dict] = []
        self._exchange_ref: str | None = None      # active conversation context

    # -- introspection ----------------------------------------------------

    @property
    def speaking_ref(self) -> str | None:
        return self._lease.ref if self._lease else None

    @property
    def queue_depth(self) -> int:
        return len(self._queue)

    @property
    def event_log(self) -> list[dict]:
        return list(self._event_log)

    def snapshot(self) -> dict:
        state = "speaking" if self._lease else ("listening" if self._exchange_ref else "idle")
        return {
            "state": state,
            "exchange": self._exchange_ref,
            "speaking_ref": self.speaking_ref,
            "queued_refs": [e.ref for e in self._queue],
            "interrupted_refs": [e.ref for e in self._interrupted],
            "cycle": self._cycle,
        }

    # -- conversation context ----------------------------------------------

    def begin_exchange(self, channel: Channel, *, ref: str) -> TurnDecision:
        """Open an interaction context (e.g., Anna starts talking to Novi)."""
        self._cycle += 1
        self._exchange_ref = ref
        return self._log("exchange-begun", True, f"exchange {ref} open", channel, ref)

    # -- outbound requests ---------------------------------------------------

    def request_speak(self, channel: Channel, *, ref: str) -> TurnDecision:
        """Request the single voice lease for one utterance."""
        self._cycle += 1
        if self._lease is None:
            return self._grant(channel, ref)
        self._seq += 1
        self._queue.append(_Entry(channel=channel, ref=ref, seq=self._seq))
        return self._log("speak-queued", False, "queued", channel, ref, action="queued")

    def release_speak(self) -> TurnDecision:
        """Finish current utterance; grant next by priority, else resume."""
        self._cycle += 1
        finished = self._lease
        self._lease = None

        if self._queue:
            top = min(self._queue, key=lambda e: (_prio(e.channel), e.seq))
            self._queue.remove(top)
            return self._grant(
                top.channel,
                top.ref,
                kind="release-next",
                reason=f"after-{finished.ref if finished else 'idle'}",
            )

        if self._interrupted:
            back = self._interrupted.pop()  # most recent first (LIFO)
            entry = _Entry(channel=back.channel, ref=back.ref, seq=0)
            self._lease = entry
            return self._log(
                "release-resume", True, f"resume {back.ref}", back.channel, back.ref
            )

        if finished is not None and self._exchange_ref == finished.ref:
            self._exchange_ref = None
        return self._log("release-idle", False, "queue-empty", finished.channel if finished else None,
                         finished.ref if finished else "")

    # -- inbound notifications -------------------------------------------------

    def notify_inbound(self, channel: Channel, *, ref: str) -> TurnDecision:
        """Higher-priority inbound arrives -> yield-after-sentence semantics.

        Applies when an utterance lease is held OR an exchange is in flight
        (speech pending/being processed): the in-flight sentence finishes
        first, the inbound is queued, and explicit resume bookkeeping runs.
        """
        self._cycle += 1
        if self._lease is None:
            if self._exchange_ref is not None:
                # Mid-exchange but between utterances (listening/processing):
                # same social contract — finish the beat, take the message.
                self._seq += 1
                self._queue.append(_Entry(channel=channel, ref=ref, seq=self._seq))
                return self._log(
                    "inbound-yield",
                    False,
                    "exchange-in-flight",
                    channel,
                    ref,
                    interrupted_ref=self._exchange_ref,
                    action="yield-after-sentence",
                )
            self._seq += 1
            self._queue.append(_Entry(channel=channel, ref=ref, seq=self._seq))
            return self._log("inbound-queued", False, "idle", channel, ref)

        held = self._lease
        if _prio(channel) <= _prio(held.channel):  # equal or higher interrupts
            self._interrupted.append(held)
            self._seq += 1
            self._queue.append(_Entry(channel=channel, ref=ref, seq=self._seq))
            return self._log(
                "inbound-yield",
                False,
                "higher-priority-inbound",
                channel,
                ref,
                interrupted_ref=held.ref,
                action="yield-after-sentence",
            )

        return self._log("inbound-note", False, "lower-priority", channel, ref, action="queue-only")

    # -- internals ---------------------------------------------------------------

    def _grant(
        self,
        channel: Channel,
        ref: str,
        *,
        kind: str = "speak-granted",
        reason: str = "lease-acquired",
    ) -> TurnDecision:
        self._lease = _Entry(channel=channel, ref=ref, seq=0)
        return self._log(kind, True, reason, channel, ref)

    def _log(
        self,
        kind: str,
        granted: bool,
        reason: str,
        channel: Channel | None,
        ref: str,
        *,
        interrupted_ref: str | None = None,
        action: str | None = None,
    ) -> TurnDecision:
        d = TurnDecision(
            action=action or kind.replace("speak-", "") if kind.startswith("speak-") else (action or kind),
            granted=granted,
            reason=reason,
            channel=channel,
            ref=ref,
            interrupted_ref=interrupted_ref,
        )
        self._event_log.append(
            {
                "kind": kind,
                "granted": granted,
                "reason": reason,
                "channel": channel.value if channel else None,
                "ref": ref,
                "interrupted_ref": interrupted_ref,
                "at_cycle": self._cycle,
            }
        )
        return d
