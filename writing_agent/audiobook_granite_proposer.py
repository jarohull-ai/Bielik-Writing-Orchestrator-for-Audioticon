"""Granite 4 3B annotation-only bridge for Audiobook Director.

Granite receives the deterministic segment catalog and may return metadata only.
The adapter owns source text, validation, and the final proposal status. This
module never starts Audioticon, TTS, DSP, or rendering.
"""
from __future__ import annotations

import json
import time
from typing import Any
from urllib.request import Request, urlopen

from .audiobook_annotations import (
    ensure_author_questions,
    expected_speaker,
    merge_annotations,
    segment_source,
)
from .audiobook_bielik_proposer import ANNOTATION_RESPONSE_SCHEMA

GRANITE_MODEL = "granite4:3b"
GRANITE_SYSTEM = """Jesteś konserwatywnym reżyserem metadanych audiobooka.
Tryb: annotation-only, proposal_only. Analizujesz segmenty tekstu, ale NIE
zwracasz ich treści i nie wolno Ci jej przepisywać. Zwróć wyłącznie jeden obiekt
JSON o kluczach annotations, author_questions, warnings, status.

Dodaj dokładnie jedną adnotację dla każdego segment_id, bez pomijania i bez
duplikatów. Używaj wyłącznie identyfikatorów mówców z allowed_speakers i
kanonicznych enumów podanych w żądaniu. Narracja opisowa bez sygnału mowy ma
speaker=narrator. Przy niepewnym mówcy użyj speaker=unknown i dodaj pytanie
autora zawierające segment_id. Nie zgaduj i nie twórz nowych mówców.

Nie dodawaj pola text, własnych pól, komentarzy Markdown ani statusu approved.
Zawsze ustaw status=proposed. Pauzy są liczbami całkowitymi w milisekundach,
sound_cues jest tablicą. Nie wykonuj żadnych działań audio.
"""

GRANITE_OPTIONS = {
    "temperature": 0.0,
    "top_p": 0.9,
    "repeat_penalty": 1.05,
    "num_predict": 1536,
}


def _parse_json(raw: str) -> dict[str, Any]:
    value = json.loads(raw.strip().strip("`").removeprefix("json").strip())
    if not isinstance(value, dict):
        raise ValueError("Granite nie zwrócił obiektu JSON")
    return value


def _call(model: str, system: str, user: str, seed: int, num_predict: int, timeout: int) -> tuple[dict[str, Any], str]:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "format": ANNOTATION_RESPONSE_SCHEMA,
        "options": {**GRANITE_OPTIONS, "num_predict": num_predict, "seed": seed},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read())
    return data, data.get("message", {}).get("content", "")


def _failure(model: str, project_id: str, scene_id: str, raw: str, errors: list[str], attempts: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "proposal_only",
        "annotation_only": True,
        "profile": "granite4_3b",
        "model": model,
        "project_id": project_id,
        "scene_id": scene_id,
        "raw_response": raw,
        "annotation_response": None,
        "annotations": None,
        "proposal": None,
        "validation": {"valid": False, "errors": errors, "warnings": []},
        "accepted_for_render": False,
        "text_owned_by_adapter": True,
        "attempts": attempts,
        "retry_count": max(0, len(attempts) - 1),
        "eval_duration_ns": data.get("eval_duration", 0),
        "eval_count": data.get("eval_count", 0),
    }


def propose_annotations(
    source_text: str,
    model: str = GRANITE_MODEL,
    project_id: str = "local-project",
    scene_id: str = "scene-001",
    seed: int = 42,
    num_predict: int = 1536,
    timeout: int = 180,
    max_retries: int = 2,
) -> dict[str, Any]:
    segments = segment_source(source_text)
    catalog = [{**segment, "expected_speaker_constraint": expected_speaker(segment["text"])} for segment in segments]
    user = json.dumps(
        {
            "project_id": project_id,
            "scene_id": scene_id,
            "allowed_speakers": ["narrator", "Anna", "Marek", "unknown"],
            "speaker_rule": "opis bez sygnału mowy = narrator; niejednoznaczny dialog = unknown + author_questions",
            "emotion_enum": ["neutral", "calm", "sad", "happy", "fear", "anger", "tension", "whisper", "shout"],
            "pace_enum": ["very_slow", "slow", "normal", "fast", "very_fast"],
            "pitch_enum": ["low", "normal", "high"],
            "segments": catalog,
        },
        ensure_ascii=False,
    )
    attempts: list[dict[str, Any]] = []
    raw = ""
    data: dict[str, Any] = {}
    errors: list[str] = []
    for attempt in range(max_retries + 1):
        started = time.monotonic_ns()
        try:
            data, raw = _call(model, GRANITE_SYSTEM, user, seed, num_predict, timeout)
            value = _parse_json(raw)
            value = ensure_author_questions(value, segments)
            proposal, validation = merge_annotations(source_text, value, project_id, scene_id)
            attempts.append({"attempt": attempt, "temperature": 0.0, "num_predict": num_predict, "reason": "initial" if attempt == 0 else "retry", "valid": bool(validation.get("valid")), "duration_ns": time.monotonic_ns() - started})
            if validation.get("valid"):
                return {
                    "mode": "proposal_only", "annotation_only": True, "profile": "granite4_3b", "model": model,
                    "project_id": project_id, "scene_id": scene_id, "raw_response": raw,
                    "annotations": value.get("annotations"), "annotation_response": value, "proposal": proposal,
                    "validation": validation, "accepted_for_render": False, "text_owned_by_adapter": True,
                    "attempts": attempts, "retry_count": attempt, "eval_duration_ns": data.get("eval_duration", 0),
                    "eval_count": data.get("eval_count", 0),
                }
            errors = list(validation.get("errors", [])) or ["validator_rejected_proposal"]
        except Exception as exc:
            errors = [f"granite_proposer_error:{type(exc).__name__}:{exc}"]
            attempts.append({"attempt": attempt, "temperature": 0.0, "num_predict": num_predict, "reason": "initial" if attempt == 0 else "retry", "valid": False, "duration_ns": time.monotonic_ns() - started})
            continue
        if attempt < max_retries:
            continue
    return _failure(model, project_id, scene_id, raw, errors, attempts, data)
