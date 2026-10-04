from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VerifiedSpeaker:
    speaker_id: str
    confidence: float
    known: bool
    source: str = "mock"


class SpeakerVerificationAdapter:
    """Thin adapter interface for real or mock voice verification backends."""

    def verify(self, audio_sample: Any, speaker_id: Optional[str] = None) -> VerifiedSpeaker:
        raise NotImplementedError


class MockSpeakerVerificationAdapter(SpeakerVerificationAdapter):
    def __init__(self, known_speakers: Optional[set[str]] = None):
        self.known_speakers = known_speakers or {"alice", "bob", "carol"}

    def verify(self, audio_sample: Any, speaker_id: Optional[str] = None) -> VerifiedSpeaker:
        if speaker_id is None:
            return VerifiedSpeaker(speaker_id="unknown", confidence=0.0, known=False, source="mock")
        known = speaker_id in self.known_speakers
        confidence = 0.96 if known else 0.0
        return VerifiedSpeaker(speaker_id=speaker_id, confidence=confidence, known=known, source="mock")


class RealSpeakerVerificationAdapter(SpeakerVerificationAdapter):
    """Placeholder adapter for a real voice-ID service. Implement here for enterprise integration."""

    def verify(self, audio_sample: Any, speaker_id: Optional[str] = None) -> VerifiedSpeaker:
        # Replace this with actual speaker embedding / diarization logic.
        # Example integrations: Azure Speaker Recognition, Google Speaker Diarization,
        # pyannote.audio, or a custom model pipeline.
        if speaker_id is None:
            return VerifiedSpeaker(speaker_id="unknown", confidence=0.0, known=False, source="real")
        return VerifiedSpeaker(speaker_id=speaker_id, confidence=0.92, known=True, source="real")
