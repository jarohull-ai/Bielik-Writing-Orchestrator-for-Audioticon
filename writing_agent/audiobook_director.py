"""Safe, deterministic baseline director; model proposals can be validated by the same contract."""
from __future__ import annotations

import re
from typing import Any

from .audiobook_contract import new_proposal


def _split_source(source_text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n+", source_text) if part.strip()]


def propose_audiobook_script(source_text: str, project_id: str = "local-project", scene_id: str = "scene-001",
                             voices: dict[str, str] | None = None) -> dict[str, Any]:
    """Create a conservative proposal without changing source wording.

    This is intentionally a baseline: a future Bielik call may suggest richer
    emotion/cue values, but the validator remains the authority.
    """
    voice_map = {"narrator": "pl_PL-darkman-medium", **(voices or {})}
    chunks = _split_source(source_text)
    segments: list[dict[str, Any]] = []
    questions: list[str] = []
    for index, text in enumerate(chunks):
        dialogue = text.startswith(("—", "–"))
        speaker = "unknown" if dialogue else "narrator"
        if dialogue:
            questions.append(f"segment_{index}: wskaż postać mówiącą tę kwestię")
        segments.append({
            "index": index,
            "speaker": speaker,
            "text": text,
            "voice": voice_map.get(speaker, voice_map["narrator"]),
            "emotion": "neutral",
            "pace": "normal",
            "pitch": "normal",
            "pause_before_ms": 0 if index == 0 else 400,
            "pause_after_ms": 900 if index == len(chunks) - 1 else 400,
            "sound_cues": [],
        })
    warnings = ["To propozycja reżyserska; wymaga akceptacji autora przed renderowaniem."]
    return new_proposal(project_id, scene_id, source_text, segments, questions, warnings)
