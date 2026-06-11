from __future__ import annotations

import uuid

from .models import MemoryBundle, MemoryQuery, MemoryStatus
from .storage import MemoryStore


def retrieve_memory(store: MemoryStore, query: MemoryQuery) -> MemoryBundle:
    fact_status = query.fact_status if query.fact_status is not None else MemoryStatus.ACTIVE
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

    facts = (
        store.search_facts_structured(
            query_text=query.query_text,
            subject=query.fact_subject,
            predicate=query.fact_predicate,
            object_text=query.fact_object_text,
            source_type=query.fact_source_type,
            status=fact_status,
            tags=query.tags,
            limit=query.max_results,
        )
        if query.include_facts
        else []
    )
    episodes = (
        store.search_episodes(query.query_text, limit=query.max_results)
        if query.include_episodes and (query.query_text.strip() or not has_structured_fact_filters)
        else []
    )

    parts = []
    warnings = []
    if facts:
        parts.append(f"found {len(facts)} fact(s)")
    if episodes:
        parts.append(f"found {len(episodes)} episode(s)")
    if not parts:
        parts.append("no matching memory found")
    non_active_statuses = sorted(
        {fact.status.value for fact in facts if fact.status != MemoryStatus.ACTIVE}
    )
    if non_active_statuses:
        warnings.append(
            "returned non-active fact status(es) due to explicit status filter: "
            + ", ".join(non_active_statuses)
        )

    return MemoryBundle(
        query_id=f"query_{uuid.uuid4().hex[:12]}",
        summary="; ".join(parts),
        facts=facts,
        episodes=episodes,
        warnings=warnings,
        provenance_summary="Results came from local SQLite fact and episode stores.",
    )
