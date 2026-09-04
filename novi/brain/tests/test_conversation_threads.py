"""Thread persistence + cross-session routine tests (plan 03 C-112/C-122).

Deterministic, socket-free. Real MacBrain on tmp SQLite, rebuilt on the
same database to simulate a restart (mirrors the replay harness probe).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


class _Cam:
    sequence = 0

    def close(self) -> None:
        return None

    def read(self) -> CameraFrame:
        type(self).sequence += 1
        return CameraFrame(frame_id="f", captured_at="t", width=2,
                           height=2, payload=b"f", metadata={})


def _brain(db: Path) -> MacBrain:
    return MacBrain(
        camera=_Cam(), perception=SpecialistPerception(),
        store_path=str(db),
        config=MacBrainConfig(curiosity_enabled=False,
                              initiative_enabled=False))


class ThreadPersistenceTests(unittest.TestCase):
    def test_thread_survives_restart(self) -> None:
        """C-112: after a restart the thread continues from persisted state."""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "m.db"
            first = _brain(db)
            first.start()
            try:
                first.respond("Tell me about the Model Y.")
            finally:
                first.stop()
            second = _brain(db)
            second.start()
            try:
                resp = second.respond("What about the range?")
            finally:
                second.stop()
        text = (resp["text"] or "").lower()
        self.assertTrue("model y" in text or "tesla" in text,
                        f"restarted brain continues the thread: {resp['text']!r}")

    def test_fresh_database_starts_clean(self) -> None:
        """A brand-new database has no thread to continue (no bleed)."""
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(Path(tmp) / "m.db")
            brain.start()
            try:
                resp = brain.respond("What about the range?")
            finally:
                brain.stop()
        text = (resp["text"] or "").lower()
        self.assertNotIn("model y", text)


class RoutineLearningTests(unittest.TestCase):
    REQUEST = "Recommend an interior for my car."

    def _teach(self, brain: MacBrain, *, rounds: int) -> None:
        brain.respond("I prefer dark interiors.")
        for _ in range(rounds):
            brain.respond(self.REQUEST)

    def test_routine_applies_after_repeated_sessions(self) -> None:
        """C-122: a request repeated across sessions is answered as usual."""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "m.db"
            first = _brain(db)
            first.start()
            try:
                self._teach(first, rounds=2)
            finally:
                first.stop()
            second = _brain(db)
            second.start()
            try:
                resp = second.respond(self.REQUEST)
            finally:
                second.stop()
        text = (resp["text"] or "").lower()
        self.assertIn("dark", text)
        self.assertIn("usual", text,
                      f"supported routine is voiced: {resp['text']!r}")

    def test_routine_not_applied_without_support(self) -> None:
        """C-122 negative: a one-session pattern is never assumed."""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "m.db"
            first = _brain(db)
            first.start()
            try:
                first.respond(self.REQUEST)
            finally:
                first.stop()
            second = _brain(db)
            second.start()
            try:
                resp = second.respond(self.REQUEST)
            finally:
                second.stop()
        self.assertNotIn("usual", (resp["text"] or "").lower())

    def test_routine_is_per_speaker(self) -> None:
        """S20: Alice's routine never leaks into Bob's replies."""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "m.db"
            first = _brain(db)
            first.start()
            try:
                first.respond("I prefer dark interiors.", person="alice")
                first.respond(self.REQUEST, person="alice")
                first.respond(self.REQUEST, person="alice")
            finally:
                first.stop()
            second = _brain(db)
            second.start()
            try:
                resp = second.respond(self.REQUEST, person="bob")
            finally:
                second.stop()
        self.assertNotIn("usual", (resp["text"] or "").lower())


if __name__ == "__main__":
    unittest.main()
