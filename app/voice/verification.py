from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VerifiedSpeaker:
    speaker_id: str
    confidence: float
    known: bool
    source: str = "mock"


class SpeakerVerificationAdapter:
    """Thin adapter interface for real or mock verification backends."""

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
    """Placeholder for enterprise-grade backends such as Azure, Google, or pyannote."""

    def verify(self, audio_sample: Any, speaker_id: Optional[str] = None) -> VerifiedSpeaker:
        if speaker_id is None:
            return VerifiedSpeaker(speaker_id="unknown", confidence=0.0, known=False, source="real")
        return VerifiedSpeaker(speaker_id=speaker_id, confidence=0.92, known=True, source="real")


@dataclass
class SessionEvent:
    timestamp: float
    event_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Tracks session state, authorization changes, and audit logs."""

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.events: Dict[str, List[SessionEvent]] = {}

    def create_session(self, session_id: str, primary_speaker_id: str, min_confidence: float = 0.8, temp_duration: int = 300) -> Any:
        from app.auth.models import SessionConfig

        session = SessionConfig(
            session_id=session_id,
            primary_speaker_id=primary_speaker_id,
            primary_only_mode=True,
            min_confidence=min_confidence,
            temp_authorization_duration_seconds=temp_duration,
        )
        session.ensure_primary_speaker_allowed()
        self.sessions[session_id] = session
        self.events.setdefault(session_id, [])
        self._record(session_id, "session_created", f"Session {session_id} created", {"primary_speaker_id": primary_speaker_id})
        return session

    def get_session(self, session_id: str) -> Any:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")
        self._expire_temporary_authorizations(session_id)
        return session

    def authorize_temporary_speaker(self, session_id: str, speaker_id: str, duration_seconds: Optional[int] = None) -> Any:
        session = self.get_session(session_id)
        if duration_seconds is None:
            duration_seconds = session.temp_authorization_duration_seconds
        session.allowed_speakers.add(speaker_id)
        session.primary_only_mode = False
        self._record(session_id, "speaker_authorized", f"Speaker {speaker_id} authorized", {"speaker_id": speaker_id, "duration_seconds": duration_seconds})
        return session

    def revoke_speaker(self, session_id: str, speaker_id: str) -> Any:
        session = self.get_session(session_id)
        session.allowed_speakers.discard(speaker_id)
        if session.primary_speaker_id not in session.allowed_speakers:
            session.allowed_speakers.add(session.primary_speaker_id)
        if len(session.allowed_speakers) == 1:
            session.primary_only_mode = True
        self._record(session_id, "speaker_revoked", f"Speaker {speaker_id} revoked", {"speaker_id": speaker_id})
        return session

    def restore_primary_only(self, session_id: str) -> Any:
        session = self.get_session(session_id)
        session.restore_primary_only()
        self._record(session_id, "locked_primary_only", "Restored primary-only mode", {})
        return session

    def get_events(self, session_id: str) -> List[SessionEvent]:
        self._expire_temporary_authorizations(session_id)
        return self.events.get(session_id, [])

    def _record(self, session_id: str, event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.events.setdefault(session_id, []).append(
            SessionEvent(timestamp=time.time(), event_type=event_type, message=message, details=details or {})
        )

    def _expire_temporary_authorizations(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is None:
            return
        for speaker_id in list(session.allowed_speakers):
            if speaker_id == session.primary_speaker_id:
                continue
            session.allowed_speakers.discard(speaker_id)
            self._record(session_id, "temporary_expired", f"Temporary authorization expired for speaker {speaker_id}", {"speaker_id": speaker_id})
