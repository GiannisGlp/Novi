"""Novi voice: continuous listening, speech, and autonomy-owned turn-taking.

Self-contained capability package. Reuses brain contracts (AudioFrame,
AgentInput) read-only via novi.brain imports; nothing in novi.brain depends
on this package. Spec: docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md.

Exports are resolved lazily so the package can be imported while
implementation lands module by module.
"""

_LAZY = {
    "Channel": (".turn_taking", "Channel"),
    "TurnDecision": (".turn_taking", "TurnDecision"),
    "TurnTakingPolicy": (".turn_taking", "TurnTakingPolicy"),
    "SpeechTurn": (".vad", "SpeechTurn"),
    "TurnSegmenter": (".vad", "TurnSegmenter"),
    "Transcript": (".stt", "Transcript"),
    "STTProvider": (".stt", "STTProvider"),
    "DeterministicSTTProvider": (".stt", "DeterministicSTTProvider"),
    "AudioOut": (".tts", "AudioOut"),
    "TTSProvider": (".tts", "TTSProvider"),
    "SayTTSProvider": (".tts", "SayTTSProvider"),
    "DeterministicTTSProvider": (".tts", "DeterministicTTSProvider"),
}

__all__ = list(_LAZY)


def __getattr__(name: str):
    if name in _LAZY:
        from importlib import import_module

        mod_name, attr = _LAZY[name]
        return getattr(import_module(mod_name, __name__), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
