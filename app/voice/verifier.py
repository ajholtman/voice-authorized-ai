from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class VoiceVerificationService(Protocol):
    def verify(self, audio_sample: Any, speaker_id: str | None = None) -> tuple[bool, float]:
        """Return (is_known, confidence_score)."""


class MockVoiceVerificationService:
    def __init__(self, known_speakers: set[str] | None = None):
        self.known_speakers = known_speakers or {"alice", "bob", "carol"}

    def verify(self, audio_sample: Any, speaker_id: str | None = None) -> tuple[bool, float]:
        if speaker_id is None:
            return False, 0.0
        if speaker_id in self.known_speakers:
            return True, 0.94
        return False, 0.0
