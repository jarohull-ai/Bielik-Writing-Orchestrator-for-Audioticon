from writing_agent.audiobook_annotations import expected_speaker, merge_annotations, segment_source, validate_annotations


SOURCE = "Anna spojrzała na drzwi.\n\n— Nie otwieraj — powiedział nieznany głos."


def valid_annotations():
    ids = segment_source(SOURCE)
    return {"annotations": [
        {"segment_id": ids[0]["segment_id"], "speaker": "narrator", "emotion": "tension", "pace": "normal", "pitch": "normal", "pause_after_ms": 400, "sound_cues": []},
        {"segment_id": ids[1]["segment_id"], "speaker": "unknown", "emotion": "whisper", "pace": "slow", "pitch": "low", "pause_after_ms": 900, "sound_cues": []},
    ], "author_questions": ["segment_002: Kto wypowiada tę kwestię?"], "warnings": [], "status": "proposed"}


def test_annotation_never_contains_text():
    response = valid_annotations()
    assert validate_annotations(response, segment_source(SOURCE))["valid"]
    proposal, result = merge_annotations(SOURCE, response, "p", "s")
    assert result["valid"] and proposal["segments"][0]["text"] == "Anna spojrzała na drzwi."


def test_unknown_fields_and_text_fail():
    response = valid_annotations(); response["annotations"][0]["text"] = "zmiana"
    result = validate_annotations(response, segment_source(SOURCE))
    assert not result["valid"] and any("unknown_fields:text" in e for e in result["errors"])


def test_unknown_speaker_requires_question():
    response = valid_annotations(); response["author_questions"] = []
    result = validate_annotations(response, segment_source(SOURCE))
    assert not result["valid"] and any("missing_author_question" in e for e in result["errors"])


def test_narration_cannot_be_assigned_to_character():
    response = valid_annotations(); response["annotations"][0]["speaker"] = "Marek"
    result = validate_annotations(response, segment_source(SOURCE))
    assert not result["valid"] and any("narration_misattributed:segment_001" in e for e in result["errors"])


def test_speaker_constraint_is_conservative():
    assert expected_speaker("Opis ulicy i deszczu.") == "narrator"
    assert expected_speaker("— Zaczekaj — powiedziała Anna.") == "Anna"
    assert expected_speaker("— Kto tam? — dobiegło zza drzwi.") == "unknown"


if __name__ == "__main__":
    test_annotation_never_contains_text(); test_unknown_fields_and_text_fail(); test_unknown_speaker_requires_question(); test_narration_cannot_be_assigned_to_character(); test_speaker_constraint_is_conservative()
    print("audiobook annotations: 5/5")
