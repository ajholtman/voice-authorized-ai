from __future__ import annotations

from app.auth.policy import AuthorizationPolicyEngine
from app.auth.models import SessionConfig


def test_primary_speaker_allowed():
    session = SessionConfig(session_id="s1", primary_speaker_id="alice")
    engine = AuthorizationPolicyEngine(session)

    decision = engine.evaluate_speaker("alice", confidence=0.96)
    assert decision.allowed is True
    assert decision.speaker_state == "primary"


def test_temporary_authorization_allows_secondary_speaker():
    session = SessionConfig(session_id="s2", primary_speaker_id="alice")
    engine = AuthorizationPolicyEngine(session)

    engine.authorize_temporary_speaker("bob", duration_seconds=120)
    decision = engine.evaluate_speaker("bob", confidence=0.91)
    assert decision.allowed is True
    assert decision.speaker_state == "temporary"


def test_unknown_speaker_rejected():
    session = SessionConfig(session_id="s3", primary_speaker_id="alice")
    engine = AuthorizationPolicyEngine(session)

    decision = engine.evaluate_speaker("charlie", confidence=0.93, speaker_is_known=False)
    assert decision.allowed is False
    assert decision.speaker_state == "unknown"


def test_interruption_is_blocked_during_active_response():
    session = SessionConfig(session_id="s4", primary_speaker_id="alice")
    engine = AuthorizationPolicyEngine(session)
    engine.authorize_temporary_speaker("bob", duration_seconds=180)
    engine.mark_response_active("alice")

    decision = engine.evaluate_speaker("bob", confidence=0.92, current_response_active=True)
    assert decision.allowed is False
    assert decision.speaker_state == "interrupted"


def test_restore_primary_only_mode():
    session = SessionConfig(session_id="s5", primary_speaker_id="alice")
    engine = AuthorizationPolicyEngine(session)
    engine.authorize_temporary_speaker("bob", duration_seconds=180)
    engine.restore_primary_only()

    decision = engine.evaluate_speaker("bob", confidence=0.9)
    assert decision.allowed is False
    assert decision.reason == "Primary-only mode active."
