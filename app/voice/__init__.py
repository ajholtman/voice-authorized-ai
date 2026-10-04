from __future__ import annotations

from typing import Any


class VoiceVerifier:
    def __init__(self, known_speakers: set[str] | None = None):
        self.known_speakers = known_speakers or {"alice", "bob", "charlie"}

    def verify(self, audio_sample: Any, speaker_id: str | None = None) -> tuple[bool, float]:
        if speaker_id is None:
            return False, 0.0
        if speaker_id in self.known_speakers:
            return True, 0.96
        return False, 0.0
