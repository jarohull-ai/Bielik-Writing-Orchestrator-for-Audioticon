import json

import writing_agent.audiobook_granite_proposer as granite


FAIL_CASE_SOURCE = "— Żółć, źdźbło i ćma — powiedziała Anna… — naprawdę brzmią inaczej. Marek odpowiedział: „To kwestia akcentu!”."


def test_granite_profile_is_annotation_only_and_bounded():
    assert granite.GRANITE_MODEL == "granite4:3b"
    assert granite.GRANITE_OPTIONS["temperature"] == 0.0
    assert granite.GRANITE_OPTIONS["num_predict"] == 1536
    assert "zwracasz ich treści" in granite.GRANITE_SYSTEM


def test_granite_invalid_response_fails_closed(monkeypatch):
    def fake_call(*args, **kwargs):
        return {"message": {"content": json.dumps({"annotations": [], "author_questions": [], "warnings": [], "status": "proposed"})}}, "{}"

    monkeypatch.setattr(granite, "_call", fake_call)
    result = granite.propose_annotations("Opis spokojnego poranka.", max_retries=2)
    assert result["accepted_for_render"] is False
    assert result["proposal"] is None
    assert result["retry_count"] == 2
    assert result["validation"]["valid"] is False


def test_granite_valid_annotation_keeps_source_owned_by_adapter(monkeypatch):
    def fake_call(*args, **kwargs):
        response = {"annotations": [{"segment_id": "segment_001", "speaker": "narrator", "emotion": "calm", "pace": "slow", "pitch": "normal", "pause_before_ms": 0, "pause_after_ms": 350, "sound_cues": []}], "author_questions": [], "warnings": [], "status": "proposed"}
        return {"message": {"content": json.dumps(response)}}, json.dumps(response)

    monkeypatch.setattr(granite, "_call", fake_call)
    result = granite.propose_annotations("Opis spokojnego poranka.")
    assert result["validation"]["valid"]
    assert result["proposal"]["status"] == "proposed"
    assert result["accepted_for_render"] is False
    assert result["proposal"]["segments"][0]["text"] == "Opis spokojnego poranka."


def test_granite_dialogue_mismatch_is_rejected_after_two_retries(monkeypatch):
    response = {
        "annotations": [
            {"segment_id": "segment_001", "speaker": "unknown", "emotion": "neutral", "pace": "normal", "pitch": "normal", "pause_before_ms": 500, "pause_after_ms": 0, "sound_cues": []},
            {"segment_id": "segment_002", "speaker": "Marek", "emotion": "neutral", "pace": "normal", "pitch": "normal", "pause_before_ms": 0, "pause_after_ms": 500, "sound_cues": []},
        ],
        "author_questions": [],
        "warnings": [],
        "status": "proposed",
    }

    monkeypatch.setattr(granite, "_call", lambda *args, **kwargs: ({"message": {"content": json.dumps(response)}}, json.dumps(response)))
    result = granite.propose_annotations(FAIL_CASE_SOURCE, max_retries=2)

    assert result["retry_count"] == 2
    assert len(result["attempts"]) == 3
    assert result["proposal"] is None
    assert result["accepted_for_render"] is False
    assert "speaker_mismatch:segment_001:expected_Anna" in result["validation"]["errors"]
