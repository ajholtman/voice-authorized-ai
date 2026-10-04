from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VoiceCommand:
    action: str
    target: Optional[str] = None
    duration_seconds: Optional[int] = None
    confidence: Optional[float] = None
    raw_text: str = ""


class VoiceCommandParser:
    """Simple parser for grant/revoke/lock/reset voice commands."""

    def parse(self, transcript: str) -> VoiceCommand:
        text = transcript.strip().lower()
        if not text:
            raise ValueError("Empty voice command")

        if "authorize" in text or "authorise" in text:
            target = self._extract_target(text, ["authorize", "authorise"])
            duration = self._extract_duration(text)
            return VoiceCommand(action="authorize", target=target, duration_seconds=duration, raw_text=transcript)

        if "revoke" in text or "remove" in text:
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
            idx = text.find(verb)
            if idx >= 0:
                remainder = text[idx + len(verb):].strip()
                candidate = re.sub(r"^(for|this|session|speaker|to|user|voice|the)\s+", "", remainder)
                candidate = candidate.strip()
                if candidate:
                    return candidate.replace(" ", "_")
        return None

    def _extract_duration(self, text: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*(second|seconds|minute|minutes|min|m)", text)
        if not m:
            return None
        value = int(m.group(1))
        unit = m.group(2).lower()
        if unit.startswith("minute") or unit in {"min", "m"}:
            return value * 60
        return value
