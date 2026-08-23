"""Tests: VAD-gated turn segmentation over an AudioFrame stream.

Contract under test (docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md):
- continuous listening; speech turns segmented from silence;
- end-of-turn on trailing silence >= endpoint_ms (no fixed timeouts alone);
- max utterance cap forces a turn boundary (long speech can't starve STT);
- frames carry provenance into the segment.
"""

from __future__ import annotations

from novi.brain.audio import AudioFrame
from novi.voice.vad import TurnSegmenter


def _speech_frame(rms: float = 0.5) -> AudioFrame:
    return AudioFrame(rms=rms, peak=min(1.0, rms * 1.6), speech=True)


def _silence_frame() -> AudioFrame:
    return AudioFrame(rms=0.01, peak=0.02, speech=False)


class TestTurnSegmentation:
    def test_silence_yields_no_segments(self):
        seg = TurnSegmenter()
        assert seg.feed(_silence_frame()) == []
        assert seg.feed(_silence_frame()) == []
        assert seg.pending is False

    def test_speech_opens_a_pending_turn(self):
        seg = TurnSegmenter()
        seg.feed(_speech_frame())
        assert seg.pending is True

    def test_trailing_silence_closes_turn(self):
        seg = TurnSegmenter()
        seg.feed(_speech_frame())
        seg.feed(_speech_frame())
        out = [seg.feed(_silence_frame()) for _ in range(seg.endpoint_frames)]
        closed = [s for chunk in out for s in chunk]
        assert len(closed) == 1
        assert seg.pending is False

    def test_segment_holds_frames_and_provenance(self):
        seg = TurnSegmenter()
        f1, f2 = _speech_frame(0.4), _speech_frame(0.6)
        f1.captured_at = "t1"
        f2.captured_at = "t2"
        seg.feed(f1)
        seg.feed(f2)
        for _ in range(seg.endpoint_frames):
            seg.feed(_silence_frame())
        closed = seg.closed_turns
        assert len(closed) == 1
        turn = closed[0]
        assert len(turn.frames) == 2
        assert turn.first_captured_at == "t1"
        assert turn.last_captured_at == "t2"
        assert turn.duration_frames == 2
        assert 0.0 < turn.peak_rms <= 0.6 + 1e-9

    def test_interword_pause_does_not_close_turn(self):
        seg = TurnSegmenter(endpoint_frames=3)
        seg.feed(_speech_frame())
        seg.feed(_silence_frame())  # short pause inside a sentence
        seg.feed(_speech_frame())
        assert seg.pending is True
        assert seg.closed_turns == []

    def test_max_utterance_forces_boundary_without_silence(self):
        seg = TurnSegmenter(max_utterance_frames=4)
        closed_now: list = []
        for _ in range(6):
            out = seg.feed(_speech_frame())
            closed_now.extend(out)
        assert len(closed_now) == 1, "boundary must be forced at the cap"
        assert seg.pending is True, "speech continues into the next turn"
        forced = closed_now[0]
        assert forced.forced_by_cap is True
        assert len(forced.frames) == 4

    def test_closed_turns_accumulate_and_drain(self):
        seg = TurnSegmenter(endpoint_frames=1)
        seg.feed(_speech_frame())
        seg.feed(_silence_frame())
        seg.feed(_speech_frame())
        seg.feed(_silence_frame())
        first = seg.drain_closed()
        assert len(first) == 2
        assert seg.drain_closed() == []

    def test_reset_clears_state(self):
        seg = TurnSegmenter()
        seg.feed(_speech_frame())
        seg.reset()
        assert seg.pending is False
        assert seg.closed_turns == []
