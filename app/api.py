from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ai.orchestrator import SecureAIGateway
from app.auth.models import SessionConfig
from app.auth.policy import AuthorizationPolicyEngine
from app.voice.verifier import MockVoiceVerificationService

app = FastAPI(title="Voice Authorized AI")

sessions: Dict[str, SessionConfig] = {}
policy_engines: Dict[str, AuthorizationPolicyEngine] = {}


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
    session_id = f"session-{len(sessions) + 1}"
    session = SessionConfig(
        session_id=session_id,
        primary_speaker_id=payload.primary_speaker_id,
        primary_only_mode=True,
        min_confidence=payload.min_confidence,
        temp_authorization_duration_seconds=payload.temp_authorization_duration_seconds,
    )
    session.ensure_primary_speaker_allowed()
    sessions[session_id] = session
    policy_engines[session_id] = AuthorizationPolicyEngine(session)
    return {"session_id": session_id, "message": "Session created"}


@app.get("/sessions/{session_id}")
def get_session_state(session_id: str) -> SessionStateResponse:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
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
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    policy = policy_engines[session_id]
    policy.authorize_temporary_speaker(payload.speaker_id, payload.duration_seconds)
    return {"session_id": session_id, "authorized_speaker": payload.speaker_id, "allowed": True}


@app.post("/sessions/{session_id}/revoke")
def revoke_speaker(session_id: str, payload: SpeakerAuthRequest) -> dict:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    policy = policy_engines[session_id]
    policy.revoke_temporary_speaker(payload.speaker_id)
    return {"session_id": session_id, "revoked_speaker": payload.speaker_id, "allowed": True}


@app.post("/sessions/{session_id}/restore-primary-only")
def restore_primary_only(session_id: str) -> dict:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    policy_engines[session_id].restore_primary_only()
    return {"session_id": session_id, "mode": "primary_only"}


@app.post("/sessions/{session_id}/submit")
def submit_secure_request(session_id: str, payload: SecureRequest) -> dict:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    policy = policy_engines[session_id]
    gateway = SecureAIGateway(policy)
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

    result = {
        "allowed": True,
        "reason": decision.reason,
        "speaker_state": decision.speaker_state,
        "confidence": payload.confidence,
        "response": {
            "text": f"Secure model execution approved for {payload.speaker_id}: {payload.transcript}",
            "source": "mock",
        },
    }
    policy.mark_response_active(payload.speaker_id)
    return result
