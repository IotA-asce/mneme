from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SourceType(StrEnum):
    SENSOR_OBSERVED = "sensor_observed"
    MODEL_INFERRED = "model_inferred"
    EXECUTIVE_GENERATED = "executive_generated"
    USER_CONFIRMED = "user_confirmed"
    IMPORTED = "imported"
    SYSTEM_GENERATED = "system_generated"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CONFLICTED = "conflicted"
    SUPPRESSED = "suppressed"
    PURGED = "purged"


def validate_probability(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number between 0.0 and 1.0")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0.0 or normalized > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return normalized


def validate_confidence(value: Any, field_name: str = "confidence") -> float:
    return validate_probability(value, field_name)


def validate_salience(value: Any, field_name: str = "salience") -> float:
    return validate_probability(value, field_name)


def validate_timestamp(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a non-negative integer timestamp")
    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer timestamp")
    return value


def validate_timestamp_range(start_ts: Any, end_ts: Any) -> tuple[int, int]:
    start = validate_timestamp(start_ts, "start_ts")
    end = validate_timestamp(end_ts, "end_ts")
    if end < start:
        raise ValueError("end_ts must be greater than or equal to start_ts")
    return start, end


def parse_source_type(value: Any, field_name: str = "source_type") -> SourceType:
    if isinstance(value, SourceType):
        return value
    try:
        return SourceType(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in SourceType)
        raise ValueError(f"{field_name} must be one of: {allowed}") from exc


def parse_memory_status(value: Any, field_name: str = "status") -> MemoryStatus:
    if isinstance(value, MemoryStatus):
        return value
    try:
        return MemoryStatus(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in MemoryStatus)
        raise ValueError(f"{field_name} must be one of: {allowed}") from exc


def _required_mapping(value: Any, field_name: str = "data") -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _required(data: Mapping[str, Any], field_name: str) -> Any:
    data = _required_mapping(data)
    if field_name not in data:
        raise ValueError(f"missing required field: {field_name}")
    return data[field_name]


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _json_mapping_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of mappings")
    items = list(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError(f"{field_name} must be a list of mappings")
    return [dict(item) for item in items]


def _string_list(value: Any, field_name: str) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field_name} must be a list of strings")
    return items


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


@dataclass(slots=True)
class SalienceFeatures:
    novelty: float = 0.0
    task_relevance: float = 0.0
    social_relevance: float = 0.0
    surprise: float = 0.0
    risk: float = 0.0
    contradiction: float = 0.0
    repetition_signal: float = 0.0
    explicit_remember_flag: float = 0.0

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, validate_salience(getattr(self, name), name))

    def normalized(self) -> "SalienceFeatures":
        return SalienceFeatures(**self.to_dict())

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SalienceFeatures":
        data = _required_mapping(data)
        return cls(
            novelty=data.get("novelty", 0.0),
            task_relevance=data.get("task_relevance", 0.0),
            social_relevance=data.get("social_relevance", 0.0),
            surprise=data.get("surprise", 0.0),
            risk=data.get("risk", 0.0),
            contradiction=data.get("contradiction", 0.0),
            repetition_signal=data.get("repetition_signal", 0.0),
            explicit_remember_flag=data.get("explicit_remember_flag", 0.0),
        )


@dataclass(slots=True)
class SalienceResult:
    score: float
    decision: str
    reasons: list[str] = field(default_factory=list)
    components: dict[str, float] = field(default_factory=dict)
    explanation: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.score = validate_salience(self.score, "score")
        self.decision = _required_text(self.decision, "decision")
        self.reasons = _string_list(self.reasons, "reasons")
        self.components = _json_mapping(self.components, "components")
        self.explanation = _json_mapping(self.explanation, "explanation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "decision": self.decision,
            "reasons": list(self.reasons),
            "components": dict(self.components),
            "explanation": dict(self.explanation),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SalienceResult":
        data = _required_mapping(data)
        return cls(
            score=_required(data, "score"),
            decision=_required(data, "decision"),
            reasons=data.get("reasons", []),
            components=data.get("components", {}),
            explanation=data.get("explanation", {}),
        )


@dataclass(slots=True)
class MemoryCandidate:
    candidate_id: str
    candidate_type: str
    summary: str
    source_type: SourceType
    confidence: float
    features: SalienceFeatures
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    provenance_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.candidate_id = _required_text(self.candidate_id, "candidate_id")
        self.candidate_type = _required_text(self.candidate_type, "candidate_type")
        self.summary = _required_text(self.summary, "summary")
        self.source_type = parse_source_type(self.source_type)
        self.confidence = validate_confidence(self.confidence)
        if isinstance(self.features, Mapping):
            self.features = SalienceFeatures.from_dict(self.features)
        if not isinstance(self.features, SalienceFeatures):
            raise ValueError("features must be SalienceFeatures or a mapping")
        self.entities = _string_list(self.entities, "entities")
        self.tags = _string_list(self.tags, "tags")
        self.payload = _json_mapping(self.payload, "payload")
        self.provenance_refs = _string_list(self.provenance_refs, "provenance_refs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "summary": self.summary,
            "source_type": self.source_type.value,
            "confidence": self.confidence,
            "features": self.features.to_dict(),
            "entities": list(self.entities),
            "tags": list(self.tags),
            "payload": dict(self.payload),
            "provenance_refs": list(self.provenance_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryCandidate":
        data = _required_mapping(data)
        return cls(
            candidate_id=_required(data, "candidate_id"),
            candidate_type=_required(data, "candidate_type"),
            summary=_required(data, "summary"),
            source_type=_required(data, "source_type"),
            confidence=_required(data, "confidence"),
            features=_required(data, "features"),
            entities=data.get("entities", []),
            tags=data.get("tags", []),
            payload=data.get("payload", {}),
            provenance_refs=data.get("provenance_refs", []),
        )


@dataclass(slots=True)
class Episode:
    episode_id: str
    start_ts: int
    end_ts: int
    summary: str
    context: dict[str, Any]
    salience: float
    confidence: float
    participants: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.episode_id = _required_text(self.episode_id, "episode_id")
        self.start_ts, self.end_ts = validate_timestamp_range(self.start_ts, self.end_ts)
        self.summary = _required_text(self.summary, "summary")
        self.context = _json_mapping(self.context, "context")
        self.salience = validate_salience(self.salience)
        self.confidence = validate_confidence(self.confidence)
        self.participants = _string_list(self.participants, "participants")
        self.objects = _string_list(self.objects, "objects")
        self.provenance_refs = _string_list(self.provenance_refs, "provenance_refs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "summary": self.summary,
            "context": dict(self.context),
            "salience": self.salience,
            "confidence": self.confidence,
            "participants": list(self.participants),
            "objects": list(self.objects),
            "provenance_refs": list(self.provenance_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Episode":
        data = _required_mapping(data)
        return cls(
            episode_id=_required(data, "episode_id"),
            start_ts=_required(data, "start_ts"),
            end_ts=_required(data, "end_ts"),
            summary=_required(data, "summary"),
            context=_required(data, "context"),
            salience=_required(data, "salience"),
            confidence=_required(data, "confidence"),
            participants=data.get("participants", []),
            objects=data.get("objects", []),
            provenance_refs=data.get("provenance_refs", []),
        )


@dataclass(slots=True)
class Fact:
    fact_id: str
    subject: str
    predicate: str
    object_value: dict[str, Any]
    confidence: float
    source_type: SourceType
    status: MemoryStatus = MemoryStatus.ACTIVE
    tags: list[str] = field(default_factory=list)
    supporting_episode_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.fact_id = _required_text(self.fact_id, "fact_id")
        self.subject = _required_text(self.subject, "subject")
        self.predicate = _required_text(self.predicate, "predicate")
        self.object_value = _json_mapping(self.object_value, "object_value")
        self.confidence = validate_confidence(self.confidence)
        self.source_type = parse_source_type(self.source_type)
        self.status = parse_memory_status(self.status)
        self.tags = _string_list(self.tags, "tags")
        self.supporting_episode_ids = _string_list(self.supporting_episode_ids, "supporting_episode_ids")

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object_value": dict(self.object_value),
            "confidence": self.confidence,
            "source_type": self.source_type.value,
            "status": self.status.value,
            "tags": list(self.tags),
            "supporting_episode_ids": list(self.supporting_episode_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Fact":
        data = _required_mapping(data)
        return cls(
            fact_id=_required(data, "fact_id"),
            subject=_required(data, "subject"),
            predicate=_required(data, "predicate"),
            object_value=_required(data, "object_value"),
            confidence=_required(data, "confidence"),
            source_type=_required(data, "source_type"),
            status=data.get("status", MemoryStatus.ACTIVE),
            tags=data.get("tags", []),
            supporting_episode_ids=data.get("supporting_episode_ids", []),
        )


@dataclass(slots=True)
class MemoryQuery:
    query_text: str
    requester: str = "unknown"
    query_type: str = "general"
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    fact_subject: str = ""
    fact_predicate: str = ""
    fact_object_text: str = ""
    fact_source_type: SourceType | None = None
    fact_status: MemoryStatus | None = None
    max_results: int = 5
    include_episodes: bool = True
    include_facts: bool = True
    include_summaries: bool = True

    def __post_init__(self) -> None:
        self.query_text = _optional_text(self.query_text, "query_text")
        self.requester = _required_text(self.requester, "requester")
        self.query_type = _required_text(self.query_type, "query_type")
        self.entities = _string_list(self.entities, "entities")
        self.tags = _string_list(self.tags, "tags")
        self.fact_subject = _optional_text(self.fact_subject, "fact_subject")
        self.fact_predicate = _optional_text(self.fact_predicate, "fact_predicate")
        self.fact_object_text = _optional_text(self.fact_object_text, "fact_object_text")
        if self.fact_source_type is not None:
            self.fact_source_type = parse_source_type(self.fact_source_type, "fact_source_type")
        if self.fact_status is not None:
            self.fact_status = parse_memory_status(self.fact_status, "fact_status")
        self.max_results = _positive_int(self.max_results, "max_results")
        self.include_episodes = _bool(self.include_episodes, "include_episodes")
        self.include_facts = _bool(self.include_facts, "include_facts")
        self.include_summaries = _bool(self.include_summaries, "include_summaries")

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_text": self.query_text,
            "requester": self.requester,
            "query_type": self.query_type,
            "entities": list(self.entities),
            "tags": list(self.tags),
            "fact_subject": self.fact_subject,
            "fact_predicate": self.fact_predicate,
            "fact_object_text": self.fact_object_text,
            "fact_source_type": self.fact_source_type.value if self.fact_source_type else None,
            "fact_status": self.fact_status.value if self.fact_status else None,
            "max_results": self.max_results,
            "include_episodes": self.include_episodes,
            "include_facts": self.include_facts,
            "include_summaries": self.include_summaries,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryQuery":
        data = _required_mapping(data)
        return cls(
            query_text=_required(data, "query_text"),
            requester=data.get("requester", "unknown"),
            query_type=data.get("query_type", "general"),
            entities=data.get("entities", []),
            tags=data.get("tags", []),
            fact_subject=data.get("fact_subject", ""),
            fact_predicate=data.get("fact_predicate", ""),
            fact_object_text=data.get("fact_object_text", ""),
            fact_source_type=data.get("fact_source_type"),
            fact_status=data.get("fact_status"),
            max_results=data.get("max_results", 5),
            include_episodes=data.get("include_episodes", True),
            include_facts=data.get("include_facts", True),
            include_summaries=data.get("include_summaries", True),
        )


@dataclass(slots=True)
class MemoryBundle:
    query_id: str
    summary: str
    facts: list[Fact] = field(default_factory=list)
    episodes: list[Episode] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ranking_explanations: list[dict[str, Any]] = field(default_factory=list)
    provenance_summary: str = ""

    def __post_init__(self) -> None:
        self.query_id = _required_text(self.query_id, "query_id")
        self.summary = _required_text(self.summary, "summary")
        self.facts = [
            item if isinstance(item, Fact) else Fact.from_dict(item)
            for item in self.facts
        ]
        self.episodes = [
            item if isinstance(item, Episode) else Episode.from_dict(item)
            for item in self.episodes
        ]
        self.warnings = _string_list(self.warnings, "warnings")
        self.ranking_explanations = _json_mapping_list(
            self.ranking_explanations,
            "ranking_explanations",
        )
        self.provenance_summary = _optional_text(self.provenance_summary, "provenance_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "summary": self.summary,
            "facts": [fact.to_dict() for fact in self.facts],
            "episodes": [episode.to_dict() for episode in self.episodes],
            "warnings": list(self.warnings),
            "ranking_explanations": [dict(item) for item in self.ranking_explanations],
            "provenance_summary": self.provenance_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryBundle":
        data = _required_mapping(data)
        return cls(
            query_id=_required(data, "query_id"),
            summary=_required(data, "summary"),
            facts=data.get("facts", []),
            episodes=data.get("episodes", []),
            warnings=data.get("warnings", []),
            ranking_explanations=data.get("ranking_explanations", []),
            provenance_summary=data.get("provenance_summary", ""),
        )
