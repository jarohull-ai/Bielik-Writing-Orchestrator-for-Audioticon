"""Export a validated proposal to Audioticon's emoji-directed script text."""
from __future__ import annotations

from typing import Any

from .audiobook_validator import validate_proposal

_PACE = {"very_slow": "🐢 ", "slow": "🐢 ", "fast": "🐇 ", "very_fast": "🐇 "}
_EMOTION = {"whisper": "🤫 ", "tension": "📈 ", "fear": "📉 ", "shout": "📈 "}


def _markers(segment: dict[str, Any]) -> str:
    parts = []
    if segment["pace"] in _PACE:
        parts.append(_PACE[segment["pace"]])
    if segment["emotion"] in _EMOTION:
        parts.append(_EMOTION[segment["emotion"]])
    if segment["pause_before_ms"] >= 700:
        parts.append("🛑 ")
    elif segment["pause_before_ms"] >= 300:
        parts.append("⏸️ ")
    return "".join(parts)


def export_audioticon_script(proposal: dict[str, Any], source_text: str) -> str:
    check = validate_proposal(proposal, source_text)
    if not check["valid"]:
        raise ValueError("Nieprawidłowa propozycja Audioticon: " + ", ".join(check["errors"]))
    lines = []
    for segment in proposal["segments"]:
        speaker = segment["speaker"]
        lines.append(f"{_markers(segment)}[{speaker}] {segment['text']}")
        if segment["pause_after_ms"] >= 700:
            lines[-1] += " 🛑"
        elif segment["pause_after_ms"] >= 300:
            lines[-1] += " ⏸️"
    return "\n".join(lines)
