from __future__ import annotations

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

    def normalized(self) -> "SalienceFeatures":
        values = {name: max(0.0, min(1.0, getattr(self, name))) for name in self.__dataclass_fields__}
        return SalienceFeatures(**values)


@dataclass(slots=True)
class SalienceResult:
    score: float
    decision: str
    reasons: list[str] = field(default_factory=list)
    components: dict[str, float] = field(default_factory=dict)


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


@dataclass(slots=True)
class Fact:
    fact_id: str
    subject: str
    predicate: str
    object_value: dict[str, Any]
    confidence: float
    source_type: SourceType
    status: MemoryStatus = MemoryStatus.ACTIVE
    supporting_episode_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MemoryQuery:
    query_text: str
    requester: str = "unknown"
    query_type: str = "general"
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    max_results: int = 5
    include_episodes: bool = True
    include_facts: bool = True
    include_summaries: bool = True


@dataclass(slots=True)
class MemoryBundle:
    query_id: str
    summary: str
    facts: list[Fact] = field(default_factory=list)
    episodes: list[Episode] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provenance_summary: str = ""
