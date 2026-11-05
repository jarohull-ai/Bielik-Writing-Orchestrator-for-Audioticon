from writing_agent.audiobook_contract import source_hash
from writing_agent.audiobook_director import propose_audiobook_script
from writing_agent.audiobook_validator import validate_proposal
from writing_agent.audioticon_adapter import export_audioticon_script
from writing_agent.contract import classify_request


SOURCE = "Lena spojrzała na latarnię.\n\n— Nie podchodź bliżej — powiedział Marek."


def test_round_trip_and_hash():
    proposal = propose_audiobook_script(SOURCE, "p1", "s1")
    assert proposal["status"] == "proposed"
    assert proposal["source_text_hash"] == source_hash(SOURCE)
    check = validate_proposal(proposal, SOURCE)
    assert check["valid"]
    script = export_audioticon_script(proposal, SOURCE)
    assert "Lena spojrzała" in script and "Nie podchodź bliżej" in script
    assert classify_request("Przygotuj scenariusz audiobooka dla Audioticonu").output_mode == "AUDIOBOOK_DIRECTOR"


def test_changed_source_fails_closed():
    proposal = propose_audiobook_script(SOURCE)
    check = validate_proposal(proposal, SOURCE.replace("Marek", "Marta"))
    assert not check["valid"] and "source_hash_mismatch" in check["errors"]


def test_model_edit_cannot_pass_as_source():
    proposal = propose_audiobook_script(SOURCE)
    proposal["segments"][0]["text"] = "Lena pobiegła do latarni."
    check = validate_proposal(proposal, SOURCE)
    assert not check["valid"]


if __name__ == "__main__":
    test_round_trip_and_hash(); test_changed_source_fails_closed(); test_model_edit_cannot_pass_as_source()
    print("audiobook adapter: 3/3")
