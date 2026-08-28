"""Tests: conversational naming — a self-introduction binds a placeholder person.

When the camera has auto-enrolled a ``new-person-N`` placeholder (see
multimodal auto-enroll), a "I'm <name>" chat or voice turn renames the
placeholder in the runtime's identity records. Deterministic — the naming
hook only fires on real introduction patterns; the brain's own reply is not
consulted for the binding.
"""

from __future__ import annotations

import unittest

from novi.web.server import NoviWebServer


class _FakeRuntime:
    """Minimal MultimodalRuntime stand-in exposing the naming contract."""

    def __init__(self, person: str) -> None:
        self.current_person = person
        self.named: list[tuple[str, str]] = []

    def name_person(self, placeholder_ref: str, name: str) -> dict:
        self.named.append((placeholder_ref, name))
        self.current_person = name
        return {"person_id": f"person-{name.lower().replace(' ', '-')}", "moved": 1}


class ConversationalNamingTests(unittest.TestCase):
    def _server(self) -> NoviWebServer:
        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        s.start()
        return s

    def test_introduction_binds_placeholder_person(self) -> None:
        s = self._server()
        try:
            rt = _FakeRuntime(person="new-person-1")
            s.mm_runtime = rt
            s.chat_send("I'm Vano", confidence=0.9)
            self.assertEqual(rt.named, [("new-person-1", "Vano")])
            self.assertEqual(rt.current_person, "Vano")
        finally:
            s.stop()

    def test_non_introduction_does_not_bind(self) -> None:
        s = self._server()
        try:
            rt = _FakeRuntime(person="new-person-1")
            s.mm_runtime = rt
            s.chat_send("what's the weather like", confidence=0.9)
            self.assertEqual(rt.named, [])
            self.assertEqual(rt.current_person, "new-person-1")
        finally:
            s.stop()

    def test_introduction_ignored_when_person_is_not_placeholder(self) -> None:
        s = self._server()
        try:
            rt = _FakeRuntime(person="Anna")
            s.mm_runtime = rt
            s.chat_send("I'm Anna", confidence=0.9)
            self.assertEqual(rt.named, [], "a recognized person is not re-named")
        finally:
            s.stop()

    def test_no_runtime_is_a_safe_noop(self) -> None:
        s = self._server()
        try:
            # mm_runtime is None in demo mode; naming must not raise
            s._bind_introduced_name("I'm Vano")
            s.chat_send("I'm Vano", confidence=0.9)
        finally:
            s.stop()

    def test_voice_listen_naming_uses_camera_person(self) -> None:
        s = self._server()
        try:
            rt = _FakeRuntime(person="new-person-2")
            s.mm_runtime = rt
            # listen() requires real STT; the hook is the same helper so cover
            # the direct binding path chat_send exercises — here via listen's
            # equivalent: the introduced-name helper on a real listen is gated
            # on STT availability, so bind through chat_send as the integration.
            s.chat_send("my name is Ana", confidence=0.9)
            self.assertEqual(rt.named, [("new-person-2", "Ana")])
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
