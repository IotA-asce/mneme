from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .models import Fact, MemoryStatus, SourceType, Speakability, validate_confidence, validate_timestamp
from .storage import (
    FactConflictReport,
    MemoryReviewRecord,
    MemoryStore,
    MetaMemoryRecord,
)
from .turn_understanding import TurnType


class ReviewProposalType(StrEnum):
    CORRECTION = "correction"
    FORGET_REQUEST = "forget_request"
    CONFIRM_MEMORY = "confirm_memory"
    CONTRADICTION_CHALLENGE = "contradiction_challenge"


class ReviewStatus(StrEnum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(slots=True)
class MemoryRefExplanation:
    memory_kind: str
    memory_id: str
    exists: bool
    source_type: str | None = None
    confidence: float | None = None
    status: str | None = None
    speakability: str | None = None
    provenance_summary: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        self.memory_kind = _required_text(self.memory_kind, "memory_kind")
        self.memory_id = _required_text(self.memory_id, "memory_id")
        if self.confidence is not None:
            self.confidence = validate_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_kind": self.memory_kind,
            "memory_id": self.memory_id,
            "exists": self.exists,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "status": self.status,
            "speakability": self.speakability,
            "provenance_summary": self.provenance_summary,
            "notes": self.notes,
        }


@dataclass(slots=True)
class MemoryReviewReport:
    explanation_id: str
    created_ts: int
    response_text: str
    memory_refs: list[MemoryRefExplanation] = field(default_factory=list)
    summary: str = ""

    def __post_init__(self) -> None:
        self.explanation_id = _required_text(self.explanation_id, "explanation_id")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.response_text = _required_text(self.response_text, "response_text")

    def to_dict(self) -> dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "created_ts": self.created_ts,
            "response_text": self.response_text,
            "memory_refs": [ref.to_dict() for ref in self.memory_refs],
            "summary": self.summary,
        }


@dataclass(slots=True)
class CorrectionProposal:
    proposal_id: str
    proposal_type: str
    created_ts: int
    text: str
    status: str = ReviewStatus.PROPOSED.value
    review_id: str | None = None
    related_memory_refs: list[dict[str, str]] = field(default_factory=list)
    reason: str = "user_review_request"

    def __post_init__(self) -> None:
        self.proposal_id = _required_text(self.proposal_id, "proposal_id")
        self.proposal_type = _required_text(self.proposal_type, "proposal_type")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.text = _required_text(self.text, "text")
        self.status = _required_text(self.status, "status")
        if self.review_id is None:
            self.review_id = self.proposal_id
        else:
            self.review_id = _required_text(self.review_id, "review_id")
        self.related_memory_refs = _memory_refs(self.related_memory_refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "review_id": self.review_id,
            "proposal_type": self.proposal_type,
            "created_ts": self.created_ts,
            "text": self.text,
            "status": self.status,
            "related_memory_refs": [dict(ref) for ref in self.related_memory_refs],
            "reason": self.reason,
        }


@dataclass(slots=True)
class MemoryReviewActionResult:
    review_id: str
    action: str
    status: str
    changed_memory_refs: list[dict[str, str]] = field(default_factory=list)
    skipped_memory_refs: list[dict[str, str]] = field(default_factory=list)
    created_fact_ids: list[str] = field(default_factory=list)
    conflict_reports: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def __post_init__(self) -> None:
        self.review_id = _required_text(self.review_id, "review_id")
        self.action = _required_text(self.action, "action")
        self.status = _required_text(self.status, "status")
        self.changed_memory_refs = _memory_refs(self.changed_memory_refs)
        self.skipped_memory_refs = _memory_refs(self.skipped_memory_refs)
        self.created_fact_ids = [
            _required_text(item, "created_fact_id") for item in self.created_fact_ids
        ]
        if self.error is not None:
            self.error = _required_text(self.error, "error")

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "action": self.action,
            "status": self.status,
            "changed_memory_refs": [dict(ref) for ref in self.changed_memory_refs],
            "skipped_memory_refs": [dict(ref) for ref in self.skipped_memory_refs],
            "created_fact_ids": list(self.created_fact_ids),
            "conflict_reports": [dict(report) for report in self.conflict_reports],
            "error": self.error,
        }


def explain_last_response(
    store: MemoryStore,
    utterance: Any | None,
    *,
    created_ts: int,
) -> MemoryReviewReport:
    if utterance is None:
        return MemoryReviewReport(
            explanation_id=f"review_{created_ts}_none",
            created_ts=created_ts,
            response_text="No previous response.",
            memory_refs=[],
            summary="There is no previous response to explain yet.",
        )
    plan = getattr(utterance, "plan", None)
    text = getattr(utterance, "text", None) or "No previous response."
    refs = _memory_refs(getattr(plan, "memory_refs", []) if plan is not None else [])
    explanations = explain_memory_refs(store, refs)
    if not explanations:
        summary = "The previous response used current-turn context or a deterministic template, not a durable memory reference."
    else:
        summary = "The previous response was grounded in " + ", ".join(
            f"{item.memory_kind} {item.memory_id}" for item in explanations
        ) + "."
    return MemoryReviewReport(
        explanation_id=f"review_{created_ts}_{_stable_id(text)}",
        created_ts=created_ts,
        response_text=text,
        memory_refs=explanations,
        summary=summary,
    )


def explain_memory_refs(
    store: MemoryStore,
    refs: Sequence[Mapping[str, Any]],
) -> list[MemoryRefExplanation]:
    explanations = []
    for ref in _memory_refs(refs):
        kind = ref["memory_kind"]
        memory_id = ref["memory_id"]
        item = _lookup_memory(store, kind, memory_id)
        meta = store.get_meta_memory(memory_id, kind)
        if item is None and meta is None:
            explanations.append(MemoryRefExplanation(kind, memory_id, exists=False, notes="memory reference was not found"))
            continue
        confidence = getattr(item, "confidence", None)
        status = getattr(getattr(item, "status", None), "value", None)
        if status is None and hasattr(item, "status"):
            status = str(getattr(item, "status"))
        source_type = (
            getattr(getattr(item, "source_type", None), "value", None)
            or (meta.source_type.value if meta is not None else None)
        )
        try:
            provenance = store.get_provenance_chain(memory_id, kind)
            provenance_summary = provenance.get("summary")
        except (KeyError, ValueError):
            provenance_summary = None
        explanations.append(
            MemoryRefExplanation(
                memory_kind=kind,
                memory_id=memory_id,
                exists=True,
                source_type=source_type,
                confidence=confidence,
                status=status,
                speakability=meta.speakability.value if meta is not None else Speakability.NORMAL.value,
                provenance_summary=provenance_summary,
            )
        )
    return explanations


def create_correction_proposal(
    text: str,
    *,
    turn_type: TurnType | str,
    created_ts: int,
    related_memory_refs: Sequence[Mapping[str, Any]] | None = None,
) -> CorrectionProposal:
    turn = turn_type if isinstance(turn_type, TurnType) else TurnType(turn_type)
    proposal_type = {
        TurnType.FORGET_REQUEST: "forget_request",
        TurnType.CONTRADICTION_CHALLENGE: "contradiction_challenge",
    }.get(turn, "correction")
    return CorrectionProposal(
        proposal_id=f"proposal_{created_ts}_{_stable_id(text)}",
        proposal_type=proposal_type,
        created_ts=created_ts,
        text=text,
        related_memory_refs=_memory_refs(related_memory_refs or []),
    )


def create_memory_review_record(
    store: MemoryStore,
    text: str,
    *,
    turn_type: TurnType | str,
    created_ts: int,
    related_memory_refs: Sequence[Mapping[str, Any]] | None = None,
) -> MemoryReviewRecord:
    turn = turn_type if isinstance(turn_type, TurnType) else TurnType(turn_type)
    proposal_type = _proposal_type_for_turn(turn)
    refs = _memory_refs(related_memory_refs or [])
    review_id = f"review_{created_ts}_{_stable_id(proposal_type + ':' + text)}"
    record = MemoryReviewRecord(
        review_id=review_id,
        proposal_type=proposal_type,
        status=ReviewStatus.PROPOSED.value,
        source_turn_text=text,
        related_memory_refs=refs,
        created_ts=created_ts,
        provenance={
            "source_type": SourceType.USER_CONFIRMED.value,
            "derivation_path": ["dialogue_turn", "memory_review_proposal"],
            "supporting_memory_ids": [ref["memory_id"] for ref in refs],
            "notes": "Created from a user review turn. No memory mutation has been applied.",
        },
    )
    return store.write_memory_review(record)


def reject_memory_review(
    store: MemoryStore,
    review_id: str,
    *,
    reason: str,
    now_ts: int | None = None,
) -> MemoryReviewRecord:
    record = _require_review(store, review_id)
    if record.status != ReviewStatus.PROPOSED.value:
        raise ValueError(f"memory review {review_id} is not proposed")
    now = _now_ts(now_ts)
    result = MemoryReviewActionResult(
        review_id=record.review_id,
        action="reject",
        status=ReviewStatus.REJECTED.value,
    ).to_dict()
    return store.update_memory_review(
        review_id,
        status=ReviewStatus.REJECTED.value,
        applied_ts=now,
        action_result=result,
        reason=_required_text(reason, "reason"),
        provenance=_review_provenance(record, "reject", reason),
    )


def apply_memory_review(
    store: MemoryStore,
    review_id: str,
    *,
    reason: str,
    fact_payload: Mapping[str, Any] | None = None,
    now_ts: int | None = None,
) -> MemoryReviewRecord:
    record = _require_review(store, review_id)
    now = _now_ts(now_ts)
    if record.status != ReviewStatus.PROPOSED.value:
        raise ValueError(f"memory review {review_id} is not proposed")

    if record.proposal_type == ReviewProposalType.FORGET_REQUEST.value:
        result = _apply_forget(store, record)
    elif record.proposal_type == ReviewProposalType.CONFIRM_MEMORY.value:
        result = _apply_confirm(store, record)
    elif record.proposal_type == ReviewProposalType.CORRECTION.value:
        result = _apply_correction(store, record, fact_payload=fact_payload)
    elif record.proposal_type == ReviewProposalType.CONTRADICTION_CHALLENGE.value:
        result = _apply_contradiction_review(store, record)
    else:
        result = MemoryReviewActionResult(
            review_id=record.review_id,
            action="apply",
            status=ReviewStatus.FAILED.value,
            error=f"unsupported proposal type: {record.proposal_type}",
        )

    status = ReviewStatus.FAILED.value if result.error else ReviewStatus.APPLIED.value
    return store.update_memory_review(
        review_id,
        status=status,
        applied_ts=now,
        action_result=result.to_dict(),
        reason=_required_text(reason, "reason"),
        provenance=_review_provenance(record, "apply", reason),
    )


def user_memory_review(store: MemoryStore, *, limit: int = 5) -> list[Fact]:
    facts = store.search_facts_structured(subject="user", limit=limit)
    visible: list[Fact] = []
    for fact in facts:
        meta = store.get_meta_memory(fact.fact_id, "fact")
        if meta is not None and meta.speakability != Speakability.NORMAL:
            continue
        visible.append(fact)
    return visible


def _proposal_type_for_turn(turn: TurnType) -> str:
    return {
        TurnType.FORGET_REQUEST: ReviewProposalType.FORGET_REQUEST.value,
        TurnType.CONTRADICTION_CHALLENGE: ReviewProposalType.CONTRADICTION_CHALLENGE.value,
        TurnType.CONFIRM_MEMORY_REQUEST: ReviewProposalType.CONFIRM_MEMORY.value,
    }.get(turn, ReviewProposalType.CORRECTION.value)


def _require_review(store: MemoryStore, review_id: str) -> MemoryReviewRecord:
    record = store.get_memory_review(review_id)
    if record is None:
        raise KeyError(f"memory review not found: {review_id}")
    return record


def _apply_forget(store: MemoryStore, record: MemoryReviewRecord) -> MemoryReviewActionResult:
    changed: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for ref in record.related_memory_refs:
        kind = ref["memory_kind"]
        memory_id = ref["memory_id"]
        fact = store.get_fact(memory_id) if kind == "fact" else None
        if kind == "fact" and fact is not None:
            store.set_fact_status(memory_id, MemoryStatus.SUPPRESSED)
            _append_review_note(store, memory_id, kind, record, "suppressed_by_forget_review")
            changed.append(ref)
            for episode_id in fact.supporting_episode_ids:
                if store.get_episode(episode_id) is None:
                    continue
                store.set_episode_status(episode_id, MemoryStatus.SUPPRESSED)
                _append_review_note(store, episode_id, "episode", record, "suppressed_by_forget_review")
                changed.append({"memory_kind": "episode", "memory_id": episode_id})
        elif kind == "episode" and store.get_episode(memory_id) is not None:
            store.set_episode_status(memory_id, MemoryStatus.SUPPRESSED)
            _append_review_note(store, memory_id, kind, record, "suppressed_by_forget_review")
            changed.append(ref)
        else:
            skipped.append(ref)
    return MemoryReviewActionResult(
        review_id=record.review_id,
        action="apply_forget",
        status=ReviewStatus.APPLIED.value,
        changed_memory_refs=changed,
        skipped_memory_refs=skipped,
        error=None if changed else "forget request had no suppressible memory refs",
    )


def _apply_confirm(store: MemoryStore, record: MemoryReviewRecord) -> MemoryReviewActionResult:
    changed: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for ref in record.related_memory_refs:
        if ref["memory_kind"] != "fact":
            skipped.append(ref)
            continue
        fact = store.get_fact(ref["memory_id"])
        if fact is None or fact.status == MemoryStatus.PURGED:
            skipped.append(ref)
            continue
        if fact.status == MemoryStatus.CONFLICTED:
            skipped.append(ref)
            continue
        confirmed = Fact(
            fact_id=fact.fact_id,
            subject=fact.subject,
            predicate=fact.predicate,
            object_value=fact.object_value,
            confidence=max(fact.confidence, 0.95),
            source_type=SourceType.USER_CONFIRMED,
            status=MemoryStatus.ACTIVE,
            tags=list(fact.tags),
            supporting_episode_ids=list(fact.supporting_episode_ids),
            supersedes_fact_id=fact.supersedes_fact_id,
        )
        store.upsert_fact(
            confirmed,
            source_id=record.review_id,
            derivation_path=["memory_review", "confirm_memory"],
            supporting_memory_ids=[ref["memory_id"]],
            notes="User explicitly confirmed this memory through review.",
        )
        _append_review_note(store, fact.fact_id, "fact", record, "confirmed_by_review")
        changed.append(ref)
    return MemoryReviewActionResult(
        review_id=record.review_id,
        action="apply_confirm",
        status=ReviewStatus.APPLIED.value,
        changed_memory_refs=changed,
        skipped_memory_refs=skipped,
        error=None if changed else "confirmation request had no safe confirmable fact refs",
    )


def _apply_correction(
    store: MemoryStore,
    record: MemoryReviewRecord,
    *,
    fact_payload: Mapping[str, Any] | None,
) -> MemoryReviewActionResult:
    payload = _fact_payload_from_mapping(fact_payload) if fact_payload is not None else None
    if payload is None:
        payload = _fact_payload_from_correction_text(record.source_turn_text)
    if payload is None:
        return MemoryReviewActionResult(
            review_id=record.review_id,
            action="apply_correction",
            status=ReviewStatus.FAILED.value,
            error="correction did not contain a deterministic fact payload",
        )

    fact = _fact_from_payload(payload, record)
    conflict_report = store.upsert_fact(
        fact,
        source_id=record.review_id,
        derivation_path=["memory_review", "correction_apply", "fact"],
        supporting_memory_ids=[ref["memory_id"] for ref in record.related_memory_refs],
        notes="User-applied correction from memory review.",
    )
    reports = [_conflict_report_dict(conflict_report)] if conflict_report is not None else []
    return MemoryReviewActionResult(
        review_id=record.review_id,
        action="apply_correction",
        status=ReviewStatus.APPLIED.value,
        changed_memory_refs=[{"memory_kind": "fact", "memory_id": fact.fact_id}],
        created_fact_ids=[fact.fact_id],
        conflict_reports=reports,
    )


def _apply_contradiction_review(
    store: MemoryStore,
    record: MemoryReviewRecord,
) -> MemoryReviewActionResult:
    reports: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for ref in record.related_memory_refs:
        if ref["memory_kind"] != "fact":
            continue
        fact = store.get_fact(ref["memory_id"])
        if fact is None:
            continue
        key = (fact.subject.lower(), fact.predicate.lower())
        if key in seen:
            continue
        seen.add(key)
        reports.extend(
            _conflict_report_dict(report)
            for report in store.get_fact_conflict_reports(
                subject=fact.subject,
                predicate=fact.predicate,
            )
        )
    if not reports:
        reports = [
            _conflict_report_dict(report)
            for report in store.get_fact_conflict_reports()
        ]
    return MemoryReviewActionResult(
        review_id=record.review_id,
        action="apply_contradiction_review",
        status=ReviewStatus.APPLIED.value,
        conflict_reports=reports,
        error=None if reports else "no conflict reports found",
    )


def _lookup_memory(store: MemoryStore, kind: str, memory_id: str) -> Any | None:
    if kind == "fact":
        return store.get_fact(memory_id)
    if kind == "episode":
        return store.get_episode(memory_id)
    if kind == "summary":
        for summary in store.get_memory_summaries(limit=100):
            if summary.summary_id == memory_id:
                return summary
    return None


def _memory_refs(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized = []
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        memory_kind = ref.get("memory_kind")
        memory_id = ref.get("memory_id")
        if isinstance(memory_kind, str) and memory_kind.strip() and isinstance(memory_id, str) and memory_id.strip():
            normalized.append({"memory_kind": memory_kind.strip(), "memory_id": memory_id.strip()})
    return normalized


def _append_review_note(
    store: MemoryStore,
    memory_id: str,
    memory_kind: str,
    record: MemoryReviewRecord,
    action: str,
) -> None:
    note = {
        "review_id": record.review_id,
        "proposal_type": record.proposal_type,
        "action": action,
    }
    existing = store.get_meta_memory(memory_id, memory_kind)
    if existing is None:
        source_type = SourceType.SYSTEM_GENERATED
        if memory_kind == "fact":
            fact = store.get_fact(memory_id)
            if fact is not None:
                source_type = fact.source_type
        store.write_meta_memory(
            MetaMemoryRecord(
                memory_id=memory_id,
                memory_kind=memory_kind,
                source_type=source_type,
                provenance={
                    "derivation_path": ["memory_review", action],
                    "memory_review_actions": [note],
                },
            )
        )
        return
    provenance = dict(existing.provenance)
    actions = provenance.get("memory_review_actions")
    if not isinstance(actions, list):
        actions = []
    actions.append(note)
    provenance["memory_review_actions"] = actions
    store.update_meta_memory(memory_id, memory_kind, provenance=provenance)


def _fact_payload_from_mapping(data: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None
    subject = data.get("subject")
    predicate = data.get("predicate")
    if not isinstance(subject, str) or not subject.strip():
        return None
    if not isinstance(predicate, str) or not predicate.strip():
        return None
    if "object_value" in data and isinstance(data["object_value"], Mapping):
        object_value = dict(data["object_value"])
    elif "value" in data:
        object_value = {"value": data["value"]}
    else:
        return None
    return {
        "fact_id": data.get("fact_id"),
        "subject": subject.strip(),
        "predicate": predicate.strip(),
        "object_value": object_value,
        "confidence": data.get("confidence", 0.98),
        "tags": data.get("tags", ["review_correction"]),
    }


def _fact_payload_from_correction_text(text: str) -> dict[str, Any] | None:
    normalized = " ".join(text.strip().rstrip(".").split())
    lowered = normalized.lower()
    prefixes = (
        "actually ",
        "no, ",
        "no ",
        "that is wrong, ",
        "that's wrong, ",
        "you are wrong, ",
        "you got that wrong, ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix):]
            lowered = lowered[len(prefix):]
            break
    patterns = (
        (r"^i like (.+)$", "likes"),
        (r"^i prefer (.+)$", "prefers"),
        (r"^my favorite ([a-z0-9_ -]+) is (.+)$", "favorite"),
    )
    for pattern, predicate in patterns:
        match = re.match(pattern, lowered)
        if not match:
            continue
        if predicate == "favorite":
            favorite_key = match.group(1).strip().replace(" ", "_")
            return {
                "subject": "user",
                "predicate": f"favorite_{favorite_key}",
                "object_value": {"value": match.group(2).strip()},
                "confidence": 0.98,
                "tags": ["review_correction", "preference"],
            }
        return {
            "subject": "user",
            "predicate": predicate,
            "object_value": {"value": match.group(1).strip()},
            "confidence": 0.98,
            "tags": ["review_correction", "preference"],
        }
    return None


def _fact_from_payload(payload: Mapping[str, Any], record: MemoryReviewRecord) -> Fact:
    subject = _required_text(payload.get("subject"), "subject")
    predicate = _required_text(payload.get("predicate"), "predicate")
    object_value = payload.get("object_value")
    if not isinstance(object_value, Mapping):
        raise ValueError("object_value must be a mapping")
    value = object_value.get("value", dict(object_value))
    fact_id = payload.get("fact_id")
    if not isinstance(fact_id, str) or not fact_id.strip():
        fact_id = _statement_fact_id(subject, predicate, value)
    tags = payload.get("tags", ["review_correction"])
    if isinstance(tags, str) or not isinstance(tags, Sequence):
        tags = ["review_correction"]
    return Fact(
        fact_id=fact_id,
        subject=subject,
        predicate=predicate,
        object_value=dict(object_value),
        confidence=validate_confidence(payload.get("confidence", 0.98)),
        source_type=SourceType.USER_CONFIRMED,
        status=MemoryStatus.ACTIVE,
        tags=[str(tag) for tag in tags if isinstance(tag, str) and tag.strip()],
        supporting_episode_ids=[
            ref["memory_id"]
            for ref in record.related_memory_refs
            if ref["memory_kind"] == "episode"
        ],
    )


def _statement_fact_id(subject: str, predicate: str, value: Any) -> str:
    canonical = json.dumps(
        [subject.strip().lower(), predicate.strip().lower(), value],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"fact_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:12]}"


def _conflict_report_dict(report: FactConflictReport) -> dict[str, Any]:
    return {
        "subject": report.subject,
        "predicate": report.predicate,
        "fact_ids": list(report.fact_ids),
        "active_fact_ids": list(report.active_fact_ids),
        "conflicted_fact_ids": list(report.conflicted_fact_ids),
        "superseded_fact_ids": list(report.superseded_fact_ids),
        "supersession_edges": dict(report.supersession_edges),
        "reason": report.reason,
    }


def _review_provenance(record: MemoryReviewRecord, action: str, reason: str) -> dict[str, Any]:
    provenance = dict(record.provenance)
    provenance["last_review_action"] = {
        "action": action,
        "reason": reason,
    }
    return provenance


def _now_ts(value: int | None) -> int:
    return validate_timestamp(value, "now_ts") if value is not None else int(time.time() * 1000)


def _stable_id(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:12]


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
