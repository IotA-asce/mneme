# Memory Retrieval

Status: V1 deterministic SQLite retrieval

Mneme's current retrieval layer is local and deterministic. It uses structured SQLite queries over facts and basic text search over episodes. It does not use embeddings, vector search, LLM reranking, or external services.

## Boundary

The retrieval layer owns:

- accepting `MemoryQuery` objects,
- querying local fact and episode storage,
- filtering ordinary fact retrieval to active facts by default,
- applying deterministic fact ordering,
- returning a `MemoryBundle`.

The retrieval layer does not own:

- fact extraction,
- contradiction detection,
- consolidation,
- long-term decay,
- actuator or safety behavior.

## Query Modes

`query_text` retrieval remains supported. A non-empty `query_text` searches:

- fact subject,
- fact predicate,
- fact object JSON text,
- episode summary,
- episode context JSON text.

Structured fact retrieval is additive. `MemoryQuery` supports these fact filters:

- `fact_subject`
- `fact_predicate`
- `fact_object_text`
- `fact_source_type`
- `fact_status`
- `tags`

Text filters are case-insensitive partial matches. Full exact strings also match because they are a specific partial match. `fact_source_type`, `fact_status`, and `tags` are exact enum or string-value filters.

When a structured fact query has an empty `query_text`, episode retrieval is skipped so a fact-only lookup does not accidentally return every episode.

## Status Handling

Ordinary fact retrieval defaults to:

```text
status = active
```

These statuses are not treated as ordinary active facts:

- `conflicted`
- `superseded`
- `suppressed`
- `purged`

A caller may explicitly set `MemoryQuery.fact_status` to retrieve one of those statuses for review/debug flows. When non-active facts are returned, the `MemoryBundle.warnings` field records that they came from an explicit status filter.

## Source Priority

When facts otherwise match the query similarly, ordering prefers more reliable source types:

1. `user_confirmed`
2. `imported`
3. `system_generated`
4. `executive_generated`
5. `sensor_observed`
6. `model_inferred`

Confidence still breaks ties after source priority. This keeps user-confirmed facts ahead of inferred facts when relevance is otherwise similar.

## Tags

Fact tags are persisted in the `fact_tag` table added by migration `002_fact_tags.sql`.

`Fact.tags` is optional and defaults to an empty list. `MemoryQuery.tags` filters facts that have all requested tags, case-insensitively. If a database does not yet have the `fact_tag` table, tag-filtered fact searches return no tag matches rather than failing.

## Examples

```python
from android_brain_memory import MemoryQuery, MemoryStatus, SourceType, retrieve_memory

bundle = retrieve_memory(
    store,
    MemoryQuery(
        query_text="",
        fact_subject="user",
        fact_predicate="prefers",
        fact_object_text="coffee",
        fact_source_type=SourceType.USER_CONFIRMED,
        tags=["preference"],
    ),
)

conflicts = retrieve_memory(
    store,
    MemoryQuery(
        query_text="",
        fact_subject="user",
        fact_status=MemoryStatus.CONFLICTED,
    ),
)
```

## Testing

Current tests cover:

- query-text compatibility,
- subject lookup,
- predicate lookup,
- object text lookup,
- tag filtering,
- source-type filtering,
- user-confirmed source priority over inferred facts,
- default active-status filtering,
- explicit non-active status retrieval warnings.

Useful targeted command:

```bash
python -m pytest tests/test_storage_retrieval.py
```
