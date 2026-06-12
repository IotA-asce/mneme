from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .models import Episode, Fact, MemoryBundle, MemoryQuery, MemoryStatus, SourceType, Speakability
from .storage import MemorySummaryRecord, MemoryStore, MetaMemoryRecord

RANKING_WEIGHTS = {
    "context_match": 0.30,
    "entity_match": 0.20,
    "recency": 0.15,
    "salience": 0.15,
    "confidence": 0.10,
    "source_reliability": 0.05,
    "retrieval_history_bonus": 0.05,
}

SOURCE_RELIABILITY = {
    SourceType.USER_CONFIRMED: 1.0,
    SourceType.IMPORTED: 0.85,
    SourceType.SYSTEM_GENERATED: 0.75,
    SourceType.EXECUTIVE_GENERATED: 0.65,
    SourceType.SENSOR_OBSERVED: 0.55,
    SourceType.MODEL_INFERRED: 0.35,
}

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
INTERNAL_SPEAKABILITY = {Speakability.NEVER_SAY, Speakability.INTERNAL_ONLY}


@dataclass(frozen=True, slots=True)
class RetrievalCandidate:
    memory_kind: str
    memory_id: str
    item: Fact | Episode | MemorySummaryRecord
    search_text: str
    entities: list[str]
    confidence: float
    timestamp: int | None = None
    salience: float | None = None
    source_type: SourceType | None = None


@dataclass(frozen=True, slots=True)
class RankedRetrievalCandidate:
    candidate: RetrievalCandidate
    score: float
    factors: dict[str, float]
    components: dict[str, float]
    explanation: dict[str, Any]


def retrieve_memory(store: MemoryStore, query: MemoryQuery) -> MemoryBundle:
    fact_status = query.fact_status if query.fact_status is not None else MemoryStatus.ACTIVE
    candidate_limit = max(query.max_results * 4, query.max_results, 20)
    has_structured_fact_filters = any(
        (
            query.fact_subject.strip(),
            query.fact_predicate.strip(),
            query.fact_object_text.strip(),
            query.fact_source_type is not None,
            query.fact_status is not None,
            query.tags,
        )
    )

    raw_facts = (
        store.search_facts_structured(
            query_text=query.query_text,
            subject=query.fact_subject,
            predicate=query.fact_predicate,
            object_text=query.fact_object_text,
            source_type=query.fact_source_type,
            status=fact_status,
            tags=query.tags,
            limit=candidate_limit,
        )
        if query.include_facts
        else []
    )
    raw_episodes = (
        store.search_episodes(query.query_text, limit=candidate_limit)
        if query.include_episodes and (query.query_text.strip() or not has_structured_fact_filters)
        else []
    )
    raw_summaries = (
        store.search_memory_summaries(query.query_text, limit=candidate_limit)
        if query.include_summaries and query.query_text.strip()
        else []
    )
    all_candidates = _build_retrieval_candidates(raw_facts, raw_episodes, raw_summaries)
    candidates = _filter_candidates_by_speakability(store, query, all_candidates)
    withheld_count = len(all_candidates) - len(candidates)
    ranked = rank_retrieval_candidates(
        store,
        query,
        candidates,
    )
    facts = [
        ranked_item.candidate.item
        for ranked_item in ranked
        if ranked_item.candidate.memory_kind == "fact"
    ][: query.max_results]
    episodes = [
        ranked_item.candidate.item
        for ranked_item in ranked
        if ranked_item.candidate.memory_kind == "episode"
    ][: query.max_results]
    summaries = [
        ranked_item.candidate.item
        for ranked_item in ranked
        if ranked_item.candidate.memory_kind == "summary"
    ][: query.max_results]
    returned_ids = {
        ("fact", fact.fact_id)
        for fact in facts
    } | {
        ("episode", episode.episode_id)
        for episode in episodes
    } | {
        ("summary", record.summary_id)
        for record in summaries
    }
    ranking_explanations = [
        dict(ranked_item.explanation, rank=rank)
        for rank, ranked_item in enumerate(ranked, start=1)
        if (ranked_item.candidate.memory_kind, ranked_item.candidate.memory_id) in returned_ids
    ]

    parts = []
    warnings = []
    if facts:
        parts.append(f"found {len(facts)} fact(s)")
    if episodes:
        parts.append(f"found {len(episodes)} episode(s)")
    if summaries:
        parts.append(f"found {len(summaries)} summary(ies)")
    if not parts:
        parts.append("no matching memory found")
        warnings.append("no matching memory found for this query")
    if withheld_count:
        warnings.append(f"{withheld_count} candidate(s) withheld by speakability policy")
    non_active_statuses = sorted(
        {fact.status.value for fact in facts if fact.status != MemoryStatus.ACTIVE}
    )
    if non_active_statuses:
        warnings.append(
            "returned non-active fact status(es) due to explicit status filter: "
            + ", ".join(non_active_statuses)
        )
    warnings.extend(_conflict_warnings(store, facts))
    _record_retrievals(store, returned_ids)

    return MemoryBundle(
        query_id=f"query_{uuid.uuid4().hex[:12]}",
        summary="; ".join(parts),
        facts=facts,
        episodes=episodes,
        summaries=[record.to_dict() for record in summaries],
        warnings=warnings,
        ranking_explanations=ranking_explanations,
        provenance_summary=_build_provenance_summary(store, facts, episodes, summaries),
    )


def rank_retrieval_candidates(
    store: MemoryStore,
    query: MemoryQuery,
    candidates: list[RetrievalCandidate],
) -> list[RankedRetrievalCandidate]:
    timestamps = [candidate.timestamp for candidate in candidates if candidate.timestamp is not None]
    min_ts = min(timestamps) if timestamps else None
    max_ts = max(timestamps) if timestamps else None
    ranked = [
        _rank_candidate(store, query, candidate, min_ts=min_ts, max_ts=max_ts)
        for candidate in candidates
    ]
    return sorted(
        ranked,
        key=lambda ranked_item: (
            -ranked_item.score,
            ranked_item.candidate.memory_kind,
            ranked_item.candidate.memory_id,
        ),
    )


def _filter_candidates_by_speakability(
    store: MemoryStore,
    query: MemoryQuery,
    candidates: list[RetrievalCandidate],
) -> list[RetrievalCandidate]:
    allow_internal = query.trusted_internal and query.include_internal
    visible = []
    for candidate in candidates:
        meta = store.get_meta_memory(candidate.memory_id, candidate.memory_kind)
        if meta is None:
            visible.append(candidate)
            continue
        if meta.speakability in INTERNAL_SPEAKABILITY and not allow_internal:
            continue
        visible.append(candidate)
    return visible


def _record_retrievals(store: MemoryStore, returned_ids: set[tuple[str, str]]) -> None:
    retrieved_ts = int(time.time())
    for memory_kind, memory_id in sorted(returned_ids):
        store.record_retrieval(memory_id, memory_kind, retrieved_ts=retrieved_ts)


def _rank_candidate(
    store: MemoryStore,
    query: MemoryQuery,
    candidate: RetrievalCandidate,
    *,
    min_ts: int | None,
    max_ts: int | None,
) -> RankedRetrievalCandidate:
    meta = store.get_meta_memory(candidate.memory_id, candidate.memory_kind)
    source_type = candidate.source_type or (meta.source_type if meta else None)
    factors = {
        "context_match": _context_match(query, candidate),
        "entity_match": _entity_match(query, candidate),
        "recency": _recency(candidate.timestamp, min_ts, max_ts),
        "salience": candidate.salience if candidate.salience is not None else 0.0,
        "confidence": candidate.confidence,
        "source_reliability": _source_reliability(source_type),
        "retrieval_history_bonus": _retrieval_history_bonus(meta),
    }
    components = {
        name: factors[name] * weight
        for name, weight in RANKING_WEIGHTS.items()
    }
    score = sum(components.values())
    explanation = {
        "memory_kind": candidate.memory_kind,
        "memory_id": candidate.memory_id,
        "score": round(score, 6),
        "weights": dict(RANKING_WEIGHTS),
        "factors": {name: round(value, 6) for name, value in factors.items()},
        "components": {name: round(value, 6) for name, value in components.items()},
        "matched_query_terms": sorted(_query_tokens(query) & _tokenize(candidate.search_text)),
        "matched_entities": sorted(_query_entity_tokens(query) & _candidate_entity_tokens(candidate)),
        "source_type": source_type.value if source_type else None,
        "timestamp": candidate.timestamp,
        "meta_memory": _meta_memory_summary(meta),
    }
    return RankedRetrievalCandidate(
        candidate=candidate,
        score=score,
        factors=factors,
        components=components,
        explanation=explanation,
    )


def _conflict_warnings(store: MemoryStore, facts: list[Fact]) -> list[str]:
    warnings = []
    seen_statements: set[tuple[str, str]] = set()
    for fact in facts:
        statement = (fact.subject.lower(), fact.predicate.lower())
        if statement in seen_statements:
            continue
        seen_statements.add(statement)
        reports = store.get_fact_conflict_reports(
            subject=fact.subject,
            predicate=fact.predicate,
        )
        if any(report.conflicted_fact_ids for report in reports):
            warnings.append(
                f"conflicting fact records exist for {fact.subject} {fact.predicate}"
            )
    return sorted(warnings)


def _build_provenance_summary(
    store: MemoryStore,
    facts: list[Fact],
    episodes: list[Episode],
    summaries: list[MemorySummaryRecord],
) -> str:
    returned = [
        *(("fact", fact.fact_id) for fact in facts),
        *(("episode", episode.episode_id) for episode in episodes),
        *(("summary", record.summary_id) for record in summaries),
    ]
    lines: list[str] = []
    for memory_kind, memory_id in returned:
        chain = store.get_provenance_chain(memory_id, memory_kind)
        for edge in chain["edges"]:
            line = (
                f"{edge['from_kind']} {edge['from_id']} {edge['relation']} "
                f"{edge['to_kind']} {edge['to_id']}"
            )
            if line not in lines:
                lines.append(line)
    if not returned:
        return "no memories were returned for this query"
    if not lines:
        return "results came from local SQLite stores; no stored provenance links for returned memories"
    return "; ".join(lines)


def _build_retrieval_candidates(
    facts: list[Fact],
    episodes: list[Episode],
    summaries: list[MemorySummaryRecord] | None = None,
) -> list[RetrievalCandidate]:
    candidates = []
    for fact in facts:
        candidates.append(
            RetrievalCandidate(
                memory_kind="fact",
                memory_id=fact.fact_id,
                item=fact,
                search_text=" ".join(
                    [
                        fact.subject,
                        fact.predicate,
                        json.dumps(fact.object_value, sort_keys=True),
                        " ".join(fact.tags),
                    ]
                ),
                entities=_fact_entities(fact),
                confidence=fact.confidence,
                source_type=fact.source_type,
            )
        )
    for episode in episodes:
        candidates.append(
            RetrievalCandidate(
                memory_kind="episode",
                memory_id=episode.episode_id,
                item=episode,
                search_text=" ".join(
                    [
                        episode.summary,
                        json.dumps(episode.context, sort_keys=True),
                        " ".join(episode.participants),
                        " ".join(episode.objects),
                    ]
                ),
                entities=[*episode.participants, *episode.objects],
                confidence=episode.confidence,
                timestamp=episode.end_ts,
                salience=episode.salience,
            )
        )
    for record in summaries or []:
        candidates.append(
            RetrievalCandidate(
                memory_kind="summary",
                memory_id=record.summary_id,
                item=record,
                search_text=" ".join(
                    [record.summary, record.scope_key, record.summary_type]
                ),
                entities=[],
                confidence=record.confidence,
                timestamp=record.end_ts if record.end_ts is not None else record.created_ts,
            )
        )
    return candidates


def _context_match(query: MemoryQuery, candidate: RetrievalCandidate) -> float:
    query_tokens = _query_tokens(query)
    if not query_tokens:
        return 0.0
    matched = query_tokens & _tokenize(candidate.search_text)
    return len(matched) / len(query_tokens)


def _entity_match(query: MemoryQuery, candidate: RetrievalCandidate) -> float:
    query_entities = _query_entity_tokens(query)
    if not query_entities:
        return 0.0
    matched = query_entities & _candidate_entity_tokens(candidate)
    return len(matched) / len(query_entities)


def _recency(timestamp: int | None, min_ts: int | None, max_ts: int | None) -> float:
    if timestamp is None or min_ts is None or max_ts is None:
        return 0.0
    if max_ts == min_ts:
        return 1.0
    return (timestamp - min_ts) / (max_ts - min_ts)


def _source_reliability(source_type: SourceType | None) -> float:
    if source_type is None:
        return 0.0
    return SOURCE_RELIABILITY[source_type]


def _retrieval_history_bonus(meta: MetaMemoryRecord | None) -> float:
    if meta is None:
        return 0.0
    return min(1.0, meta.retrieval_count / 10.0)


def _meta_memory_summary(meta: MetaMemoryRecord | None) -> dict[str, Any] | None:
    if meta is None:
        return None
    return {
        "last_retrieved_ts": meta.last_retrieved_ts,
        "retrieval_count": meta.retrieval_count,
        "source_type": meta.source_type.value,
    }


def _query_tokens(query: MemoryQuery) -> set[str]:
    text_parts = [
        query.query_text,
        query.fact_subject,
        query.fact_predicate,
        query.fact_object_text,
        " ".join(query.tags),
    ]
    return _tokenize(" ".join(text_parts))


def _query_entity_tokens(query: MemoryQuery) -> set[str]:
    return _tokenize(" ".join(query.entities))


def _candidate_entity_tokens(candidate: RetrievalCandidate) -> set[str]:
    return _tokenize(" ".join(candidate.entities))


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def _fact_entities(fact: Fact) -> list[str]:
    entities = [fact.subject]
    for value in fact.object_value.values():
        if isinstance(value, str):
            entities.append(value)
    return entities
