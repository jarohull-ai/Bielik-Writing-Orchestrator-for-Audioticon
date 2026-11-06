"""Common proposal envelope and manual review transitions.

The model-specific proposers remain responsible for generation. This module
owns the model-agnostic envelope and the only allowed status transitions.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from .audiobook_bielik_proposer import propose_annotations as propose_bielik_annotations
from .audiobook_contract import source_hash
from .audiobook_granite_proposer import propose_annotations as propose_granite_annotations
from .audiobook_validator import validate_proposal

PROFILES: dict[str, Callable[..., dict[str, Any]]] = {
    "bielik": propose_bielik_annotations,
    "granite4-3b": propose_granite_annotations,
}


class ProposalError(ValueError):
    """Base error for invalid or unsafe proposal operations."""


class ProposalTransitionError(ProposalError):
    """Raised when a proposal status transition is not allowed."""


def available_profiles() -> tuple[str, ...]:
    return tuple(PROFILES)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_proposal_envelope(
    profile: str,
    result: dict[str, Any],
    source_text: str,
    *,
    proposal_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Wrap either model result in one auditable, still-unapproved object."""
    if profile not in PROFILES:
        raise ProposalError(f"unknown_profile:{profile}")
    model_proposal = result.get("proposal") or {}
    validation = result.get("validation") or {"valid": False, "errors": ["missing_model_proposal"], "warnings": []}
    return {
        "proposal_id": proposal_id or f"proposal-{uuid4().hex}",
        "profile": profile,
        "status": "proposed",
        "project_id": result.get("project_id", model_proposal.get("project_id", "local-project")),
        "scene_id": result.get("scene_id", model_proposal.get("scene_id", "scene-001")),
        "source_text_hash": source_hash(source_text),
        "segments": deepcopy(model_proposal.get("segments", [])),
        "open_questions": deepcopy(model_proposal.get("open_questions", [])),
        "validation": deepcopy(validation),
        "created_at": created_at or _now(),
        "reviewed_at": None,
        "reviewer_note": None,
        "decision_history": [],
        "accepted_for_render": False,
        "annotation_only": True,
        "source_text_owned_by_adapter": True,
    }


def propose_profile(profile: str, source_text: str, **kwargs: Any) -> dict[str, Any]:
    """Generate and normalize a proposal without granting approval."""
    try:
        proposer = PROFILES[profile]
    except KeyError as exc:
        raise ProposalError(f"unknown_profile:{profile}") from exc
    result = proposer(source_text, **kwargs)
    return create_proposal_envelope(profile, result, source_text)


def validate_proposal_envelope(envelope: dict[str, Any], source_text: str) -> dict[str, Any]:
    """Revalidate hash, coverage, enums, speakers and status from current source."""
    errors: list[str] = []
    if not isinstance(envelope, dict):
        return {"valid": False, "errors": ["proposal_not_object"], "warnings": []}
    if envelope.get("status") not in {"proposed", "approved", "rejected"}:
        errors.append("invalid_review_status")
    if envelope.get("source_text_hash") != source_hash(source_text):
        errors.append("source_hash_mismatch")
    check = validate_proposal(
        {
            "project_id": envelope.get("project_id"),
            "scene_id": envelope.get("scene_id"),
            "source_text_hash": envelope.get("source_text_hash"),
            "status": "proposed" if envelope.get("status") == "proposed" else envelope.get("status"),
            "segments": envelope.get("segments"),
            "open_questions": [item for item in envelope.get("open_questions", []) if isinstance(item, str)],
            "warnings": [],
        },
        source_text,
    )
    # The model validator result is retained for audit, but acceptance uses a
    # fresh validation pass. Rejected proposals may remain invalid so the user
    # can record why they were rejected.
    errors.extend(check.get("errors", []))
    return {"valid": not errors, "errors": errors, "warnings": check.get("warnings", [])}


def _record_decision(envelope: dict[str, Any], status: str, reviewer_note: str, when: str | None) -> dict[str, Any]:
    updated = deepcopy(envelope)
    timestamp = when or _now()
    updated["status"] = status
    updated["reviewed_at"] = timestamp
    updated["reviewer_note"] = reviewer_note
    updated.setdefault("decision_history", []).append({"from": "proposed", "to": status, "at": timestamp, "reviewer_note": reviewer_note})
    updated["accepted_for_render"] = False
    return updated


def approve_proposal(envelope: dict[str, Any], source_text: str, reviewer_note: str, *, reviewed_at: str | None = None) -> dict[str, Any]:
    """Approve only a currently proposed, freshly valid envelope."""
    if envelope.get("status") != "proposed":
        raise ProposalTransitionError(f"transition_not_allowed:{envelope.get('status')}->approved")
    if not reviewer_note or not reviewer_note.strip():
        raise ProposalError("reviewer_note_required")
    validation = validate_proposal_envelope(envelope, source_text)
    if not validation["valid"]:
        raise ProposalError("approval_blocked:" + ";".join(validation["errors"]))
    return _record_decision(envelope, "approved", reviewer_note.strip(), reviewed_at)


def reject_proposal(envelope: dict[str, Any], source_text: str, reviewer_note: str, *, reviewed_at: str | None = None) -> dict[str, Any]:
    """Record a user rejection; it cannot later be promoted or reopened."""
    if envelope.get("status") != "proposed":
        raise ProposalTransitionError(f"transition_not_allowed:{envelope.get('status')}->rejected")
    if not reviewer_note or not reviewer_note.strip():
        raise ProposalError("reviewer_note_required")
    return _record_decision(envelope, "rejected", reviewer_note.strip(), reviewed_at)


def rejection_reasons(envelope: dict[str, Any], source_text: str) -> list[str]:
    """Return current validator reasons plus recorded model reasons."""
    current = validate_proposal_envelope(envelope, source_text)
    recorded = envelope.get("validation", {}).get("errors", []) if isinstance(envelope.get("validation"), dict) else []
    return list(dict.fromkeys([*recorded, *current.get("errors", [])]))
