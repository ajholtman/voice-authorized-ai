from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.auth.policy import AuthorizationDecision, AuthorizationPolicyEngine
from app.auth.models import SessionConfig


@dataclass
class AIRequest:
    session_id: str
    speaker_id: str
    transcript: str
    confidence: float
    source: str = "voice"


class SecureAIGateway:
    def __init__(self, policy_engine: AuthorizationPolicyEngine, llm_client: Optional[Any] = None):
        self.policy_engine = policy_engine
        self.llm_client = llm_client

    def process_request(self, request: AIRequest) -> Dict[str, Any]:
        if not self.policy_engine.config:
            raise ValueError("No active session configured for secure AI processing.")

        decision = self.policy_engine.evaluate_speaker(
            speaker_id=request.speaker_id,
            confidence=request.confidence,
            current_response_active=self.policy_engine.config.aktive_response,
            speaker_is_known=True,
        )

        if not decision.allowed:
            return {
                "allowed": False,
                "reason": decision.reason,
                "speaker_state": decision.speaker_state,
                "confidence": decision.confidence,
                "response": None,
            }

        if self.llm_client is None:
            response = {
                "text": f"LLM request approved for {request.speaker_id}: {request.transcript}",
                "source": "mock",
            }
        else:
            response = self.llm_client.generate(request.transcript)

        self.policy_engine.mark_response_active(request.speaker_id)
        return {
            "allowed": True,
            "reason": decision.reason,
            "speaker_state": decision.speaker_state,
            "confidence": decision.confidence,
            "response": response,
        }
