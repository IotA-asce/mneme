from __future__ import annotations

import uuid

from .models import MemoryBundle, MemoryQuery
from .storage import MemoryStore


def retrieve_memory(store: MemoryStore, query: MemoryQuery) -> MemoryBundle:
    facts = store.search_facts(query.query_text, limit=query.max_results) if query.include_facts else []
    episodes = store.search_episodes(query.query_text, limit=query.max_results) if query.include_episodes else []

    parts = []
    if facts:
        parts.append(f"found {len(facts)} fact(s)")
    if episodes:
        parts.append(f"found {len(episodes)} episode(s)")
    if not parts:
        parts.append("no matching memory found")

    return MemoryBundle(
        query_id=f"query_{uuid.uuid4().hex[:12]}",
        summary="; ".join(parts),
        facts=facts,
        episodes=episodes,
        provenance_summary="Results came from local SQLite fact and episode stores.",
    )
