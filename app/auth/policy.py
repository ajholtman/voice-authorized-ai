from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Set
import time

from app.auth.models import SessionConfig


@dataclass
class AuthorizationDecision:
    allowed: bool
    reason: str
    speaker_state: str
    confidence: float


class AuthorizationPolicyEngine:
    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config

    def attach_session(self, session: SessionConfig) -> None:
        self.config = session
        self.config.ensure_primary_speaker_allowed()

    def set_primary_speaker(self, speaker_id: str) -> None:
        if not self.config:
            raise ValueError("No session is attached.")
        self.config.primary_speaker_id = speaker_id
        self.config.primary_only_mode = True
        self.config.allowed_speakers = {speaker_id}

    def authorize_temporary_speaker(self, speaker_id: str, duration_seconds: Optional[int] = None) -> None:
        if not self.config:
            raise ValueError("No session is attached.")
        if duration_seconds is None:
            duration_seconds = self.config.temp_authorization_duration_seconds

        self.config.primary_only_mode = False
        self.config.allowed_speakers.add(speaker_id)

    def revoke_temporary_speaker(self, speaker_id: str) -> None:
        if not self.config:
            raise ValueError("No session is attached.")
        self.config.allowed_speakers.discard(speaker_id)
        if self.config.primary_speaker_id not in self.config.allowed_speakers:
            self.config.allowed_speakers.add(self.config.primary_speaker_id)
        if len(self.config.allowed_speakers) == 1:
            self.config.primary_only_mode = True

    def restore_primary_only(self) -> None:
        if not self.config:
            raise ValueError("No session is attached.")
        self.config.restore_primary_only()

    def mark_response_active(self, speaker_id: str) -> None:
        if not self.config:
            raise ValueError("No session is attached.")
        self.config.aktive_response = True
        self.config.current_response_owner = speaker_id

    def end_response(self) -> None:
        if not self.config:
            raise ValueError("No session is attached.")
        self.config.aktive_response = False
        self.config.current_response_owner = None

    def evaluate_speaker(
        self,
        speaker_id: str,
        confidence: float,
        current_response_active: bool = False,
        speaker_is_known: bool = True,
    ) -> AuthorizationDecision:
        if not self.config:
            raise ValueError("No session is attached.")

        if speaker_is_known is False:
            return AuthorizationDecision(
                allowed=False,
                reason="Unknown or uncertain speaker.",
                speaker_state="unknown",
                confidence=confidence,
            )

        if confidence < self.config.min_confidence:
            return AuthorizationDecision(
                allowed=False,
                reason="Confidence below threshold.",
                speaker_state="uncertain",
                confidence=confidence,
            )

        if speaker_id == self.config.primary_speaker_id:
            return AuthorizationDecision(
                allowed=True,
                reason="Primary speaker allowed.",
                speaker_state="primary",
                confidence=confidence,
            )

        if speaker_id in self.config.allowed_speakers:
            if current_response_active and self.config.current_response_owner and speaker_id != self.config.current_response_owner:
                return AuthorizationDecision(
                    allowed=False,
                    reason="Unauthorized interruption detected.",
                    speaker_state="interrupted",
                    confidence=confidence,
                )
            return AuthorizationDecision(
                allowed=True,
                reason="Temporarily authorized speaker allowed.",
                speaker_state="temporary",
                confidence=confidence,
            )

        if self.config.primary_only_mode:
            return AuthorizationDecision(
                allowed=False,
                reason="Primary-only mode active.",
                speaker_state="blocked",
                confidence=confidence,
            )

        return AuthorizationDecision(
            allowed=False,
            reason="Speaker is not authorized for this session.",
            speaker_state="denied",
            confidence=confidence,
        )
