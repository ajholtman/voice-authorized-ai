from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ai.orchestrator import SecureAIGateway
from app.auth.models import SessionConfig
from app.auth.policy import AuthorizationPolicyEngine
from app.voice.commands import VoiceCommandParser
from app.voice.verification import SessionManager

app = FastAPI(title="Voice Authorized AI")

manager = SessionManager()


class SessionCreateRequest(BaseModel):
    primary_speaker_id: str = Field(..., min_length=1)
    min_confidence: float = 0.8
    temp_authorization_duration_seconds: int = 300


class SpeakerAuthRequest(BaseModel):
    speaker_id: str = Field(..., min_length=1)
    duration_seconds: Optional[int] = None


class SecureRequest(BaseModel):
    speaker_id: str = Field(..., min_length=1)
    transcript: str = Field(..., min_length=1)
    confidence: float = 0.0


class VoiceCommandRequest(BaseModel):
    transcript: str = Field(..., min_length=1)


class SessionStateResponse(BaseModel):
    session_id: str
    primary_speaker_id: str
    allowed_speakers: List[str]
    primary_only_mode: bool
    min_confidence: float
    active_response: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "voice-authorized-ai"}


@app.post("/sessions")
def create_session(payload: SessionCreateRequest) -> dict:
    session_id = f"session-{len(manager.sessions) + 1}"
    session = manager.create_session(
        session_id=session_id,
        primary_speaker_id=payload.primary_speaker_id,
        min_confidence=payload.min_confidence,
        temp_duration=payload.temp_authorization_duration_seconds,
    )
    return {"session_id": session_id, "message": "Session created"}


@app.get("/sessions/{session_id}")
def get_session_state(session_id: str) -> SessionStateResponse:
    session = manager.get_session(session_id)
    return SessionStateResponse(
        session_id=session.session_id,
        primary_speaker_id=session.primary_speaker_id,
        allowed_speakers=sorted(session.allowed_speakers),
        primary_only_mode=session.primary_only_mode,
        min_confidence=session.min_confidence,
        active_response=session.aktive_response,
    )


@app.post("/sessions/{session_id}/authorize")
def authorize_speaker(session_id: str, payload: SpeakerAuthRequest) -> dict:
    manager.authorize_temporary_speaker(session_id, payload.speaker_id, payload.duration_seconds)
    return {"session_id": session_id, "authorized_speaker": payload.speaker_id, "allowed": True}


@app.post("/sessions/{session_id}/revoke")
def revoke_speaker(session_id: str, payload: SpeakerAuthRequest) -> dict:
    manager.revoke_speaker(session_id, payload.speaker_id)
    return {"session_id": session_id, "revoked_speaker": payload.speaker_id, "allowed": True}


@app.post("/sessions/{session_id}/restore-primary-only")
def restore_primary_only(session_id: str) -> dict:
    manager.restore_primary_only(session_id)
    return {"session_id": session_id, "mode": "primary_only"}


@app.post("/sessions/{session_id}/voice-command")
def voice_command(session_id: str, payload: VoiceCommandRequest) -> dict:
    parser = VoiceCommandParser()
    command = parser.parse(payload.transcript)
    session = manager.get_session(session_id)

    if command.action == "authorize":
        duration = command.duration_seconds or session.temp_authorization_duration_seconds
        session.allowed_speakers.add(command.target or "unknown")
        session.primary_only_mode = False
        return {"session_id": session_id, "action": "authorize", "target": command.target, "duration_seconds": duration}

    if command.action == "revoke":
        session.allowed_speakers.discard(command.target or "")
        return {"session_id": session_id, "action": "revoke", "target": command.target}

    if command.action == "lock_primary":
        manager.restore_primary_only(session_id)
        return {"session_id": session_id, "action": "lock_primary"}

    if command.action == "reset":
        manager.restore_primary_only(session_id)
        return {"session_id": session_id, "action": "reset"}

    return {"session_id": session_id, "action": command.action, "result": "processed"}


@app.post("/sessions/{session_id}/submit")
def submit_secure_request(session_id: str, payload: SecureRequest) -> dict:
    session = manager.get_session(session_id)
    policy = AuthorizationPolicyEngine(session)
    decision = policy.evaluate_speaker(
        speaker_id=payload.speaker_id,
        confidence=payload.confidence,
        current_response_active=session.aktive_response,
        speaker_is_known=True,
    )

    if not decision.allowed:
        return {
            "allowed": False,
            "reason": decision.reason,
            "speaker_state": decision.speaker_state,
            "confidence": payload.confidence,
            "response": None,
        }

    policy.mark_response_active(payload.speaker_id)
    return {
        "allowed": True,
        "reason": decision.reason,
        "speaker_state": decision.speaker_state,
        "confidence": payload.confidence,
        "response": {
            "text": f"Secure model execution approved for {payload.speaker_id}: {payload.transcript}",
            "source": "mock",
        },
    }


@app.get("/sessions/{session_id}/events")
def get_events(session_id: str) -> dict:
    events = manager.get_events(session_id)
    return {"session_id": session_id, "events": [{"timestamp": e.timestamp, "event_type": e.event_type, "message": e.message, "details": e.details} for e in events]}
