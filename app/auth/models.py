from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class SpeakerRecord:
    speaker_id: str
    display_name: str | None = None
    verified: bool = False
    confidence: float = 0.0
    temporary: bool = False
    expires_at: float | None = None


@dataclass
class SessionConfig:
    session_id: str
    primary_speaker_id: str
    allowed_speakers: Set[str] = field(default_factory=set)
    primary_only_mode: bool = True
    unknown_speaker_mode: str = "deny"
    min_confidence: float = 0.8
    temp_authorization_duration_seconds: int = 300
    aktive_response: bool = False
    current_response_owner: str | None = None

    def ensure_primary_speaker_allowed(self) -> None:
        self.allowed_speakers.add(self.primary_speaker_id)

    def restore_primary_only(self) -> None:
        self.primary_only_mode = True
        self.allowed_speakers = {self.primary_speaker_id}
        self.current_response_owner = None
        self.aktive_response = False
