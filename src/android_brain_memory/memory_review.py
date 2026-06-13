from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .models import Fact, Speakability, validate_confidence, validate_timestamp
from .storage import MemoryStore
from .turn_understanding import TurnType


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
    status: str = "proposed_not_applied"
    related_memory_refs: list[dict[str, str]] = field(default_factory=list)
    reason: str = "user_review_request"

    def __post_init__(self) -> None:
        self.proposal_id = _required_text(self.proposal_id, "proposal_id")
        self.proposal_type = _required_text(self.proposal_type, "proposal_type")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.text = _required_text(self.text, "text")
        self.status = _required_text(self.status, "status")
        self.related_memory_refs = _memory_refs(self.related_memory_refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_type": self.proposal_type,
            "created_ts": self.created_ts,
            "text": self.text,
            "status": self.status,
            "related_memory_refs": [dict(ref) for ref in self.related_memory_refs],
            "reason": self.reason,
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


def user_memory_review(store: MemoryStore, *, limit: int = 5) -> list[Fact]:
    facts = store.search_facts_structured(subject="user", limit=limit)
    visible: list[Fact] = []
    for fact in facts:
        meta = store.get_meta_memory(fact.fact_id, "fact")
        if meta is not None and meta.speakability != Speakability.NORMAL:
            continue
        visible.append(fact)
    return visible


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


def _stable_id(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:12]


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
