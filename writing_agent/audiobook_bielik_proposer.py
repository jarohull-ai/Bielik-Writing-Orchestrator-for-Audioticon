"""Bielik proposal-only bridge for Audiobook Director.

This module only asks Ollama for a JSON proposal and validates it. It has no
audio, filesystem-bible, Audioticon, TTS or DSP side effects.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen
from typing import Any

from .audiobook_contract import source_hash
from .audiobook_annotations import expected_speaker, merge_annotations, segment_source
from .audiobook_validator import validate_proposal

PROPOSAL_SYSTEM = """Jesteś reżyserem audiobooka w trybie proposal_only.
Zachowaj tekst źródłowy znak w znak: nie poprawiaj gramatyki, nie zmieniaj dialogów,
nie dopisuj wydarzeń, postaci ani zdań i nie zmieniaj kolejności. Możesz proponować
wyłącznie speaker, voice, emotion, pace, pitch, pause_before_ms, pause_after_ms
oraz sound_cues. Jeśli mówcy nie da się ustalić, użyj speaker=unknown_character
i dodaj author_question z pytaniem dla autora. Zwróć wyłącznie JSON zgodny z
kontraktem. Odpowiedź musi mieć dokładnie klucze project_id, scene_id,
source_text_hash, status, segments, open_questions i warnings. Każdy element
segments musi mieć index, speaker, text, voice, emotion, pace, pitch,
pause_before_ms, pause_after_ms i sound_cues. Nie używaj approved.
Wzór: {"project_id":"...","scene_id":"...","source_text_hash":"64-znakowy-hash","status":"proposed","segments":[{"index":0,"speaker":"narrator","text":"dokładny fragment źródła","voice":"pl_PL-darkman-medium","emotion":"neutral","pace":"normal","pitch":"normal","pause_before_ms":0,"pause_after_ms":400,"sound_cues":[]}],"open_questions":[],"warnings":[]}
"""

ANNOTATION_SYSTEM = """Jesteś reżyserem audiobooka w trybie annotation_only.
Nie zwracaj pola text i nie powtarzaj żadnego tekstu źródłowego. Tekst jest
właścicielem adaptera. Zwróć tablicę JSON adnotacji, po jednej dla każdego
 segment_id. Każda adnotacja ma dokładnie pola: segment_id, speaker, emotion,
 pace, pitch, pause_after_ms, sound_cues; może mieć pause_before_ms i
author_questions są na poziomie obiektu odpowiedzi, nie w adnotacji. Identyfikatory
speaker muszą być dokładnie: narrator, Anna, Marek albo unknown. Nie zmieniaj
pisowni. emotion neutral/calm/sad/happy/fear/anger/tension/whisper/shout; pace
very_slow/slow/normal/fast/very_fast;
pitch low/normal/high. Dla unknown dodaj pytanie w tablicy author_questions.
Nie dodawaj
żadnych innych kluczy. Klucz na wysokość głosu to dokładnie pitch, nigdy pitches.
pause_after_ms musi być liczbą całkowitą, nigdy null; sound_cues musi być tablicą
obiektów w formacie {"type":"dsp_preset","name":"cathedral:kaplica"},
albo pustą tablicą; nigdy null i nigdy zwykłym tekstem. Dozwolone nazwy presetów:
radio:wojskowe, cathedral:kaplica, whisper:intymny, robot:ciezki.
Odpowiedź ma mieć dokładnie: annotations, author_questions, warnings, status.
Przykład: {"annotations":[{"segment_id":"segment_001","speaker":"narrator","emotion":"neutral","pace":"normal","pitch":"normal","pause_before_ms":0,"pause_after_ms":400,"sound_cues":[]}],"author_questions":[],"warnings":[],"status":"proposed"}. Zwróć wyłącznie ten obiekt JSON.
"""

PROPOSAL_SCHEMA = {
    "type": "object",
    "required": ["project_id", "scene_id", "source_text_hash", "status", "segments", "open_questions", "warnings"],
    "properties": {
        "project_id": {"type": "string"}, "scene_id": {"type": "string"},
        "source_text_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "status": {"type": "string", "enum": ["proposed"]},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "segments": {"type": "array", "items": {"type": "object", "required": ["index", "speaker", "text", "voice", "emotion", "pace", "pitch", "pause_before_ms", "pause_after_ms", "sound_cues"], "properties": {
            "index": {"type": "integer"}, "speaker": {"type": "string"}, "text": {"type": "string"}, "voice": {"type": "string"},
            "emotion": {"type": "string"}, "pace": {"type": "string"}, "pitch": {"type": "string"}, "pause_before_ms": {"type": "integer"}, "pause_after_ms": {"type": "integer"}, "sound_cues": {"type": "array"}
        }}}
    }
}

ANNOTATION_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["annotations", "author_questions", "warnings", "status"],
    "properties": {
        "annotations": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["segment_id", "speaker", "emotion", "pace", "pitch", "pause_before_ms", "pause_after_ms", "sound_cues"],
            "properties": {
                "segment_id": {"type": "string"},
                "speaker": {"type": "string", "enum": ["narrator", "Anna", "Marek", "unknown"]},
                "emotion": {"type": "string", "enum": ["neutral", "calm", "sad", "happy", "fear", "anger", "tension", "whisper", "shout"]},
                "pace": {"type": "string", "enum": ["very_slow", "slow", "normal", "fast", "very_fast"]},
                "pitch": {"type": "string", "enum": ["low", "normal", "high"]},
                "pause_before_ms": {"type": "integer", "minimum": 0, "maximum": 10000},
                "pause_after_ms": {"type": "integer", "minimum": 0, "maximum": 10000},
                "sound_cues": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["type", "name"], "properties": {"type": {"type": "string", "enum": ["dsp_preset"]},
                    "name": {"type": "string", "enum": ["radio:wojskowe", "cathedral:kaplica", "whisper:intymny", "robot:ciezki"]}}}}
            }
        }},
        "author_questions": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "status": {"type": "string", "enum": ["proposed"]}
    }
}


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].lstrip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Bielik nie zwrócił obiektu JSON")
        try:
            value = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Niepoprawny JSON Bielika: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Odpowiedź Bielika nie jest obiektem JSON")
    return value


def _call(model: str, user: str, seed: int, num_predict: int, timeout: int) -> tuple[dict[str, Any], str]:
    payload = {"model": model, "messages": [{"role": "system", "content": PROPOSAL_SYSTEM}, {"role": "user", "content": user}],
               "stream": False, "options": {"temperature": 0.0, "seed": seed, "num_predict": num_predict}}
    request = Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read())
    return data, data.get("message", {}).get("content", "")


def propose(source_text: str, model: str = "bielik-4.5b-v3:q5", project_id: str = "local-project",
            scene_id: str = "scene-001", seed: int = 42, num_predict: int = 2048, timeout: int = 180) -> dict[str, Any]:
    user = json.dumps({"project_id": project_id, "scene_id": scene_id, "source_text_hash": source_hash(source_text),
                       "known_speakers": ["narrator", "anna", "marek", "unknown_character"], "source_text": source_text}, ensure_ascii=False)
    raw = ""
    data: dict[str, Any] = {}
    try:
        data, raw = _call(model, user, seed, num_predict, timeout)
        proposal = _extract_json(raw)
        # The bridge may not repair content, but it always prevents model approval.
        proposal["status"] = "proposed"
        validation = validate_proposal(proposal, source_text)
        return {"mode": "proposal_only", "model": model, "project_id": project_id, "scene_id": scene_id,
                "raw_response": raw, "proposal": proposal, "validation": validation,
                "accepted_for_render": False, "eval_duration_ns": data.get("eval_duration", 0), "eval_count": data.get("eval_count", 0)}
    except Exception as exc:
        return {"mode": "proposal_only", "model": model, "project_id": project_id, "scene_id": scene_id,
                "raw_response": raw, "annotations": None, "proposal": None,
                "validation": {"valid": False, "errors":[f"annotation_proposer_error:{type(exc).__name__}:{exc}"], "warnings": []},
                "accepted_for_render": False, "text_owned_by_adapter": True, "eval_duration_ns": data.get("eval_duration", 0), "eval_count": data.get("eval_count", 0)}


def propose_annotations(source_text: str, model: str = "bielik-4.5b-v3:q5", project_id: str = "local-project",
                        scene_id: str = "scene-001", seed: int = 42, num_predict: int = 2048, timeout: int = 180) -> dict[str, Any]:
    segments = segment_source(source_text)
    catalog = [{**segment, "expected_speaker_constraint": expected_speaker(segment["text"])} for segment in segments]
    user = json.dumps({"project_id": project_id, "scene_id": scene_id,
                       "allowed_speakers": ["narrator", "Anna", "Marek"],
                       "speaker_rule": "opis bez sygnału mowy = narrator; niejednoznaczny dialog = unknown + author_questions",
                       "segments": catalog}, ensure_ascii=False)
    raw = ""; data: dict[str, Any] = {}
    try:
        payload = {"model": model, "messages": [{"role": "system", "content": ANNOTATION_SYSTEM}, {"role": "user", "content": user}],
                   "stream": False, "format": ANNOTATION_RESPONSE_SCHEMA,
                   "options": {"temperature": 0.0, "seed": seed, "num_predict": num_predict}}
        request = Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read())
        raw = data.get("message", {}).get("content", "")
        value = json.loads(raw.strip().strip("`").removeprefix("json").strip())
        if not isinstance(value, dict):
            raise ValueError("Odpowiedź Bielika nie jest obiektem JSON")
        proposal, validation = merge_annotations(source_text, value, project_id, scene_id)
        return {"mode": "proposal_only", "annotation_only": True, "model": model, "project_id": project_id, "scene_id": scene_id,
                "raw_response": raw, "annotations": value.get("annotations") if isinstance(value, dict) else None,
                "annotation_response": value, "proposal": proposal, "validation": validation,
                "accepted_for_render": False, "text_owned_by_adapter": True, "eval_duration_ns": data.get("eval_duration", 0), "eval_count": data.get("eval_count", 0)}
    except Exception as exc:
        return {"mode": "proposal_only", "model": model, "project_id": project_id, "scene_id": scene_id,
                "raw_response": raw, "annotation_response": None, "annotations": None, "proposal": None, "validation": {"valid": False, "errors":[f"proposer_error:{type(exc).__name__}:{exc}"], "warnings": []},
                "accepted_for_render": False, "eval_duration_ns": data.get("eval_duration", 0), "eval_count": data.get("eval_count", 0)}
