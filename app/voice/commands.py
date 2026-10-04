from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VoiceCommand:
    action: str
    target: Optional[str] = None
    duration_seconds: Optional[int] = None
    raw_text: str = ""


class VoiceCommandParser:
    """Parses grant/revoke/lock/reset voice commands used by the authorization layer."""

    def parse(self, transcript: str) -> VoiceCommand:
        text = transcript.strip().lower()
        if not text:
            raise ValueError("Empty voice command")

        if re.search(r"\b(authorize|authorise)\b", text):
            target = self._extract_target(text, ["authorize", "authorise"])
            duration = self._extract_duration(text)
            return VoiceCommand(action="authorize", target=target, duration_seconds=duration, raw_text=transcript)

        if re.search(r"\b(revoke|remove)\b", text):
            target = self._extract_target(text, ["revoke", "remove"])
            return VoiceCommand(action="revoke", target=target, raw_text=transcript)

        if "lock" in text and "primary" in text:
            return VoiceCommand(action="lock_primary", raw_text=transcript)

        if "reset" in text or "restore" in text:
            return VoiceCommand(action="reset", raw_text=transcript)

        if "unknown" in text and "speaker" in text:
            return VoiceCommand(action="toggle_unknown_mode", raw_text=transcript)

        raise ValueError(f"Unsupported command: {transcript}")

    def _extract_target(self, text: str, verbs: List[str]) -> Optional[str]:
        for verb in verbs:
            match = re.search(rf"\b{verb}\b\s+(.*?)(?:\s+for\b|$)", text)
            if match:
                candidate = match.group(1).strip()
                if candidate:
                    return candidate.replace(" ", "_")
        return None

    def _extract_duration(self, text: str) -> Optional[int]:
        match = re.search(r"(\d+)\s*(second|seconds|minute|minutes|min|m)", text)
        if not match:
            return None
        value = int(match.group(1))
        unit = match.group(2).lower()
        if unit.startswith("minute") or unit in {"min", "m"}:
            return value * 60
        return value
