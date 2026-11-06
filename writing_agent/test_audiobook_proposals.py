import pytest

from writing_agent.audiobook_annotations import segment_source
from writing_agent.audiobook_proposals import (
    ProposalError,
    ProposalTransitionError,
    approve_proposal,
    available_profiles,
    create_proposal_envelope,
    reject_proposal,
    rejection_reasons,
    validate_proposal_envelope,
)
import writing_agent.audiobook_proposals as proposals


SOURCE = "Anna spojrzała na drzwi."


def result_for(profile="bielik"):
    return {
        "profile": profile,
        "project_id": "p",
        "scene_id": "s",
        "proposal": {
            "project_id": "p",
            "scene_id": "s",
            "segments": [{
                "index": 0, "segment_id": "segment_001", "speaker": "narrator", "text": SOURCE,
                "voice": "pl_PL-darkman-medium", "emotion": "neutral", "pace": "normal", "pitch": "normal",
                "pause_before_ms": 0, "pause_after_ms": 350, "sound_cues": [],
            }],
        },
        "validation": {"valid": True, "errors": [], "warnings": []},
    }


def test_profiles_share_one_registry_and_envelope():
    assert available_profiles() == ("bielik", "granite4-3b")
    envelope = create_proposal_envelope("bielik", result_for(), SOURCE, proposal_id="proposal-test", created_at="2026-11-06T00:00:00Z")
    assert envelope["status"] == "proposed"
    assert envelope["profile"] == "bielik"
    assert envelope["accepted_for_render"] is False
    assert validate_proposal_envelope(envelope, SOURCE)["valid"]


def test_common_dispatch_normalizes_both_profiles(monkeypatch):
    calls = []

    def fake(profile):
        def _propose(source_text, **kwargs):
            calls.append((profile, source_text))
            return result_for(profile)
        return _propose

    monkeypatch.setitem(proposals.PROFILES, "bielik", fake("bielik"))
    monkeypatch.setitem(proposals.PROFILES, "granite4-3b", fake("granite4-3b"))
    bielik = proposals.propose_profile("bielik", SOURCE)
    granite = proposals.propose_profile("granite4-3b", SOURCE)
    assert [bielik["profile"], granite["profile"]] == ["bielik", "granite4-3b"]
    assert calls == [("bielik", SOURCE), ("granite4-3b", SOURCE)]


def test_approval_requires_fresh_validation_and_note():
    envelope = create_proposal_envelope("granite4-3b", result_for("granite4-3b"), SOURCE)
    approved = approve_proposal(envelope, SOURCE, "Ręcznie sprawdzone.", reviewed_at="2026-11-06T01:00:00Z")
    assert approved["status"] == "approved"
    assert approved["accepted_for_render"] is False
    assert approved["decision_history"][0]["to"] == "approved"
    with pytest.raises(ProposalTransitionError):
        approve_proposal(approved, SOURCE, "ponownie")
    with pytest.raises(ProposalTransitionError):
        reject_proposal(approved, SOURCE, "odrzucam")


def test_rejection_is_terminal_and_auditable():
    envelope = create_proposal_envelope("bielik", result_for(), SOURCE)
    rejected = reject_proposal(envelope, SOURCE, "Mówca wymaga korekty.", reviewed_at="2026-11-06T01:00:00Z")
    assert rejected["status"] == "rejected"
    assert rejected["reviewer_note"] == "Mówca wymaga korekty."
    with pytest.raises(ProposalTransitionError):
        approve_proposal(rejected, SOURCE, "zmiana decyzji")


def test_changed_source_and_invalid_proposal_cannot_be_approved():
    envelope = create_proposal_envelope("bielik", result_for(), SOURCE)
    assert "source_hash_mismatch" in validate_proposal_envelope(envelope, "Inny tekst.")["errors"]
    with pytest.raises(ProposalError, match="approval_blocked"):
        approve_proposal(envelope, "Inny tekst.", "Nie zatwierdzam starego tekstu.")
    reasons = rejection_reasons(envelope, "Inny tekst.")
    assert "source_hash_mismatch" in reasons


def test_invalid_transition_and_missing_note_are_blocked():
    envelope = create_proposal_envelope("bielik", result_for(), SOURCE)
    with pytest.raises(ProposalError, match="reviewer_note_required"):
        reject_proposal(envelope, SOURCE, "")
    with pytest.raises(ProposalTransitionError):
        approve_proposal({**envelope, "status": "rejected"}, SOURCE, "nie")
