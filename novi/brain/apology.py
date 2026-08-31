"""Mature apology architecture (plan 24, Phase 11).

A mature apology has four components (plan §15):

  recognition → responsibility → correction → follow-through

Repeated apologies are an anti-pattern ("I'm very sorry." / "I sincerely
apologize." / "I deeply regret..."). One appropriate acknowledgement is
normally enough — the builder suppresses a second apology in the same
conversation.

Deterministic and hardware-free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .affective_evidence import utc_now_iso


@dataclass
class Apology:
    """One mature apology with the four plan §15 components."""

    recognition: str
    responsibility: str
    correction: str
    follow_through: str
    at: str = ""

    def render(self) -> str:
        """Render a mature apology — no groveling, no repeated regret."""
        return (
            f"You're right. {self.recognition}. {self.responsibility}. "
            f"{self.correction}. {self.follow_through}."
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "recognition": self.recognition,
            "responsibility": self.responsibility,
            "correction": self.correction,
            "follow_through": self.follow_through,
            "at": self.at,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "Apology":
        return cls(
            recognition=str(data.get("recognition", "")),
            responsibility=str(data.get("responsibility", "")),
            correction=str(data.get("correction", "")),
            follow_through=str(data.get("follow_through", "")),
            at=str(data.get("at", "")),
        )


class ApologyBuilder:
    """Builds apologies and suppresses repeated apologies (plan §11)."""

    def __init__(self, *, max_apologies: int = 1) -> None:
        self.max_apologies = max_apologies
        self.apology_count = 0

    def build(
        self,
        *,
        recognition: str,
        responsibility: str,
        correction: str,
        follow_through: str,
    ) -> Apology | None:
        """Return an Apology, or None when repeated apologies are suppressed."""
        if self.apology_count >= self.max_apologies:
            return None
        self.apology_count += 1
        return Apology(
            recognition=recognition,
            responsibility=responsibility,
            correction=correction,
            follow_through=follow_through,
            at=utc_now_iso(),
        )
