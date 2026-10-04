from __future__ import annotations

import time

from app.auth.models import SessionConfig
from app.auth.policy import AuthorizationDecision, AuthorizationPolicyEngine


class TestPolicyEngine:
    """A thin test wrapper used to validate the core authorization state machine."""

    def __init__(self):
        self.session = SessionConfig(
            session_id="demo-session",
            primary_speaker_id="alice",
            primary_only_mode=True,
            min_confidence=0.8,
            temp_authorization_duration_seconds=300,
        )
        self.engine = AuthorizationPolicyEngine(self.session)

    def run(self):
        decision = self.engine.evaluate_speaker("alice", confidence=0.96)
        assert decision.allowed is True

        decision = self.engine.evaluate_speaker("bob", confidence=0.95)
        assert decision.allowed is False

        self.engine.authorize_temporary_speaker("bob", duration_seconds=120)
        decision = self.engine.evaluate_speaker("bob", confidence=0.95)
        assert decision.allowed is True

        self.engine.mark_response_active("alice")
        intrusion = self.engine.evaluate_speaker("bob", confidence=0.95, current_response_active=True)
        assert intrusion.allowed is False

        self.engine.restore_primary_only()
        assert self.session.primary_only_mode is True

        return {"status": "ok", "session_id": self.session.session_id}
