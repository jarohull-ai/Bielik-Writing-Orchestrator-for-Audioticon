"""Annotation-only contract: Bielik can describe segments, never own their text."""
from __future__ import annotations

import re
from typing import Any

from .audiobook_contract import ALLOWED_EMOTIONS, ALLOWED_LEVELS, ALLOWED_PACES, ALLOWED_PRESETS, ALLOWED_SPEAKERS, new_proposal
from .audiobook_validator import validate_proposal

ANNOTATION_FIELDS = {"segment_id", "speaker", "emotion", "pace", "pitch", "pause_before_ms", "pause_after_ms", "sound_cues"}
REQUIRED_ANNOTATION_FIELDS = {"segment_id", "speaker", "emotion", "pace", "pause_after_ms", "sound_cues"}
RESPONSE_FIELDS = {"annotations", "author_questions", "warnings", "status"}


def segment_source(source_text: str) -> list[dict[str, Any]]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", source_text) if part.strip()]
    parts = []
    for paragraph in paragraphs:
        # Keep narration and a following dash/quote dialogue as separate local
        # segments. Whitespace between segments is still verified by the source
        # coverage validator; no source characters are regenerated.
        parts.extend(piece.strip() for piece in re.split(
            r"(?<=[.!?])\s+(?=(?:[—–„\"]|(?:Anna|Marek)\s+"
            r"(?:powiedziała|powiedział|zapytała|zapytał|szepnęła|szepnął|"
            r"krzyknęła|krzyknął|odpowiedziała|odpowiedział)\b))", paragraph
        ) if piece.strip())
    return [{"segment_id": f"segment_{index + 1:03d}", "index": index, "text": text} for index, text in enumerate(parts)]


def expected_speaker(text: str) -> str:
    """Conservative speaker constraint; it never guesses from narrative content."""
    stripped = text.strip()
    leading_attribution = re.match(
        r"^(Anna|Marek)\s+(?:powiedziała|powiedział|zapytała|zapytał|"
        r"szepnęła|szepnął|krzyknęła|krzyknął|odpowiedziała|odpowiedział)\b",
        stripped,
    )
    if leading_attribution:
        return leading_attribution.group(1)
    dialogue = stripped.startswith(("—", "–", "„", '"'))
    if not dialogue:
        return "narrator"
    match = re.search(r"\b(Anna|Marek)\b\s+(?:powiedziała|powiedział|zapytała|zapytał|szepnęła|szepnął|krzyknęła|krzyknął|odpowiedziała|odpowiedział)", text)
    if not match:
        # Do not scan through later narration: a later name must not replace
        # the first explicit speaker attribution.
        match = re.search(r'(?:powiedziała|powiedział|zapytała|zapytał|szepnęła|szepnął|krzyknęła|krzyknął|odpowiedziała|odpowiedział)\s+\b(Anna|Marek)\b', text)
    return match.group(1) if match else "unknown"


def ensure_author_questions(response: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Add only an explicit segment-scoped question; never infer a speaker."""
    questions = response.get("author_questions")
    if not isinstance(questions, list):
        questions = []
        response["author_questions"] = questions
    warnings = response.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
        response["warnings"] = warnings
    segment_ids = {segment["segment_id"] for segment in segments}
    for annotation in response.get("annotations", []):
        if not isinstance(annotation, dict) or annotation.get("speaker") != "unknown":
            continue
        segment_id = annotation.get("segment_id")
        if segment_id in segment_ids and not any(segment_id in str(question) for question in questions):
            questions.append(f"{segment_id}: Kto wypowiada ten fragment?")
            warnings.append(f"adapter_added_author_question:{segment_id}")
    return response


def validate_annotations(response: Any, segments: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(response, dict):
        return {"valid": False, "errors": ["response_not_object"], "warnings": []}
    unknown_response = sorted(set(response) - RESPONSE_FIELDS)
    if unknown_response:
        errors.append(f"unknown_response_fields:{','.join(unknown_response)}")
    for field in ("annotations", "author_questions", "warnings"):
        if not isinstance(response.get(field), list):
            errors.append(f"invalid_response_field:{field}")
    if response.get("status") != "proposed":
        errors.append("invalid_annotation_status")
    annotations = response.get("annotations") if isinstance(response.get("annotations"), list) else []
    author_questions = response.get("author_questions") if isinstance(response.get("author_questions"), list) else []
    if not all(isinstance(item, str) for item in author_questions):
        errors.append("invalid_author_questions")
    expected = {segment["segment_id"] for segment in segments}
    seen: set[str] = set()
    for annotation in annotations:
        if not isinstance(annotation, dict):
            errors.append("annotation_not_object")
            continue
        unknown = sorted(set(annotation) - ANNOTATION_FIELDS)
        if unknown:
            errors.append(f"unknown_fields:{','.join(unknown)}")
        missing = sorted(REQUIRED_ANNOTATION_FIELDS - set(annotation))
        if missing:
            errors.append(f"missing_fields:{','.join(missing)}")
        segment_id = annotation.get("segment_id")
        if segment_id not in expected:
            errors.append(f"unknown_segment_id:{segment_id}")
        if segment_id in seen:
            errors.append(f"duplicate_segment_id:{segment_id}")
        seen.add(segment_id)
        if annotation.get("speaker") not in ALLOWED_SPEAKERS:
            errors.append(f"unknown_speaker_id:{annotation.get('speaker')}")
        if annotation.get("emotion") not in ALLOWED_EMOTIONS:
            errors.append(f"invalid_emotion:{annotation.get('emotion')}")
        if annotation.get("pace") not in ALLOWED_PACES:
            errors.append(f"invalid_pace:{annotation.get('pace')}")
        if annotation.get("pitch", "normal") not in ALLOWED_LEVELS:
            errors.append(f"invalid_pitch:{annotation.get('pitch')}")
        for field in ("pause_before_ms", "pause_after_ms"):
            if field in annotation and (not isinstance(annotation[field], int) or not 0 <= annotation[field] <= 10000):
                errors.append(f"invalid_{field}:{segment_id}")
        if not isinstance(annotation.get("sound_cues"), list):
            errors.append(f"invalid_sound_cues:{segment_id}")
        else:
            for cue in annotation["sound_cues"]:
                if not isinstance(cue, dict) or cue.get("type") != "dsp_preset" or cue.get("name") not in ALLOWED_PRESETS:
                    errors.append(f"invalid_dsp_preset:{segment_id}")
        if annotation.get("speaker") == "unknown" and not any(segment_id in item for item in author_questions):
            errors.append(f"missing_author_question:{segment_id}")
        segment_text = next((item["text"] for item in segments if item["segment_id"] == segment_id), "")
        expected_role = expected_speaker(segment_text)
        if expected_role == "narrator" and annotation.get("speaker") != "narrator":
            errors.append(f"narration_misattributed:{segment_id}")
        elif expected_role in {"Anna", "Marek"} and annotation.get("speaker") != expected_role:
            errors.append(f"speaker_mismatch:{segment_id}:expected_{expected_role}")
        elif expected_role == "unknown" and annotation.get("speaker") != "unknown":
            errors.append(f"speaker_uncertain_without_unknown:{segment_id}")
    missing_ids = sorted(expected - seen)
    if missing_ids:
        errors.append("missing_segment_annotations:" + ",".join(missing_ids))
    return {"valid": not errors, "errors": errors, "warnings": []}


def merge_annotations(source_text: str, response: dict[str, Any], project_id: str, scene_id: str,
                      voices: dict[str, str] | None = None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    segments = segment_source(source_text)
    check = validate_annotations(response, segments)
    if not check["valid"]:
        return None, check
    annotations = response["annotations"]
    author_questions = response["author_questions"]
    voice_map = {"narrator": "pl_PL-darkman-medium", "Anna": "pl-PL-ZofiaNeural", "Marek": "pl-PL-MarekNeural", "unknown": "pl_PL-darkman-medium", **(voices or {})}
    by_id = {item["segment_id"]: item for item in annotations}
    merged = []
    questions = []
    for segment in segments:
        annotation = by_id[segment["segment_id"]]
        item = {"index": segment["index"], "segment_id": segment["segment_id"], "speaker": annotation["speaker"], "text": segment["text"],
                "voice": voice_map.get(annotation["speaker"], "pl_PL-darkman-medium"), "emotion": annotation["emotion"],
                "pace": annotation["pace"], "pitch": annotation.get("pitch", "normal"),
                "pause_before_ms": annotation.get("pause_before_ms", 0), "pause_after_ms": annotation["pause_after_ms"],
                "sound_cues": annotation["sound_cues"]}
        merged.append(item)
        questions.extend(item for item in author_questions if segment["segment_id"] in item)
    proposal = new_proposal(project_id, scene_id, source_text, merged, questions,
                            ["Adnotacje wygenerowane przez Bielika; wymagają ręcznej akceptacji."])
    proposal_check = validate_proposal(proposal, source_text)
    return proposal, proposal_check
