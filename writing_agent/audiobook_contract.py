"""Contract for the proposal exchanged between Writing Agent and Audioticon."""
from __future__ import annotations

import hashlib
import json
from typing import Any

ALLOWED_EMOTIONS = {"neutral", "calm", "sad", "happy", "fear", "anger", "tension", "whisper", "shout"}
ALLOWED_PACES = {"very_slow", "slow", "normal", "fast", "very_fast"}
ALLOWED_LEVELS = {"low", "normal", "high"}
ALLOWED_STATUSES = {"proposed", "approved_fixture", "approved"}
ALLOWED_SPEAKERS = {"narrator", "Anna", "Marek", "unknown"}
ALLOWED_PRESETS = {"radio:wojskowe", "cathedral:kaplica", "whisper:intymny", "robot:ciezki"}


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_proposal(project_id: str, scene_id: str, source_text: str, segments: list[dict[str, Any]],
                 open_questions: list[str] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "scene_id": scene_id,
        "source_text_hash": source_hash(source_text),
        "status": "proposed",
        "segments": segments,
        "open_questions": open_questions or [],
        "warnings": warnings or [],
    }


def dumps(proposal: dict[str, Any]) -> str:
    return json.dumps(proposal, ensure_ascii=False, indent=2)
