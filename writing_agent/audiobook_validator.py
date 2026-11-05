"""Fail-closed validation for Audioticon director proposals."""
from __future__ import annotations

import re
from typing import Any

from .audiobook_contract import ALLOWED_EMOTIONS, ALLOWED_LEVELS, ALLOWED_PACES, ALLOWED_PRESETS, ALLOWED_SPEAKERS, ALLOWED_STATUSES, source_hash


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _ordered_coverage(source: str, segments: list[dict[str, Any]]) -> bool:
    cursor = 0
    for segment in segments:
        text = segment.get("text")
        if not isinstance(text, str) or not text.strip():
            return False
        found = source.find(text, cursor)
        if found >= 0:
            if _normal(source[cursor:found]):
                return False
            cursor = found + len(text)
            continue
        # Segmenters may trim paragraph whitespace, but never words or punctuation.
        compact_source = _normal(source[cursor:])
        compact_text = _normal(text)
        if not compact_source.startswith(compact_text):
            return False
        cursor = len(source)
    return _normal(source[cursor:]) == ""


def validate_proposal(proposal: dict[str, Any], source_text: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = {"project_id", "scene_id", "source_text_hash", "status", "segments", "open_questions", "warnings"}
    missing = sorted(required - set(proposal))
    if missing:
        errors.append(f"missing_fields:{','.join(missing)}")
    if proposal.get("source_text_hash") != source_hash(source_text):
        errors.append("source_hash_mismatch")
    if proposal.get("status") not in ALLOWED_STATUSES:
        errors.append("invalid_status")
    if proposal.get("status") == "approved":
        errors.append("unapproved_status")
    segments = proposal.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments_missing")
        segments = []
    if not _ordered_coverage(source_text, segments):
        errors.append("segment_text_does_not_cover_source")
    for expected_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            errors.append(f"segment_{expected_index}:not_object")
            continue
        if segment.get("index") != expected_index:
            errors.append(f"segment_{expected_index}:invalid_index")
        if segment.get("speaker") not in ALLOWED_SPEAKERS:
            errors.append(f"segment_{expected_index}:unknown_speaker_id")
        for field in ("speaker", "text", "voice", "emotion", "pace", "pitch", "pause_before_ms", "pause_after_ms", "sound_cues"):
            if field not in segment:
                errors.append(f"segment_{expected_index}:missing_{field}")
        if segment.get("emotion") not in ALLOWED_EMOTIONS:
            errors.append(f"segment_{expected_index}:invalid_emotion")
        if segment.get("pace") not in ALLOWED_PACES or segment.get("pitch") not in ALLOWED_LEVELS:
            errors.append(f"segment_{expected_index}:invalid_prosody")
        for field in ("pause_before_ms", "pause_after_ms"):
            if not isinstance(segment.get(field), int) or segment.get(field) < 0 or segment.get(field) > 10000:
                errors.append(f"segment_{expected_index}:invalid_{field}")
        if not isinstance(segment.get("sound_cues"), list):
            errors.append(f"segment_{expected_index}:invalid_sound_cues")
        else:
            for cue in segment["sound_cues"]:
                if not isinstance(cue, dict) or cue.get("type") != "dsp_preset" or cue.get("name") not in ALLOWED_PRESETS:
                    errors.append(f"segment_{expected_index}:invalid_dsp_preset")
        if segment.get("speaker") == "unknown":
            question_tokens = {f"segment_{expected_index}", f"segment_{expected_index + 1:03d}", f"segment_{expected_index + 1}"}
            if not any(any(token in str(item) for token in question_tokens) for item in proposal.get("open_questions", [])):
                errors.append(f"segment_{expected_index}:missing_author_question")
            else:
                warnings.append(f"segment_{expected_index}:speaker_needs_author_decision")
    return {"valid": not errors, "errors": errors, "warnings": warnings}
