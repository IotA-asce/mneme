# Memory Retrieval

Status: V1 deterministic SQLite retrieval

Mneme's current retrieval layer is local and deterministic. It uses structured SQLite queries over facts and basic text search over episodes. It does not use embeddings, vector search, LLM reranking, or external services.

## Boundary

The retrieval layer owns:

- accepting `MemoryQuery` objects,
- querying local fact and episode storage,
- filtering ordinary fact retrieval to active facts by default,
- filtering internal-only speakability records by default,
- building retrieval candidates,
- applying deterministic reranking,
- updating meta-memory retrieval counters for returned items,
- returning a `MemoryBundle`.

The retrieval layer does not own:

- fact extraction,
- contradiction detection,
- consolidation,
- long-term decay,
- complete authorization or encryption policy,
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

Trusted internal retrieval is explicit. To include `never_say` or `internal_only` meta-memory records, callers must set both:

- `trusted_internal=True`
- `include_internal=True`

Setting only one flag is not enough.

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

Fact conflict handling can mark inferred facts `superseded` or incompatible confirmed facts `conflicted`. Ordinary retrieval hides those facts through the same active-status default.

## Source Priority

When facts otherwise match the query similarly, ordering prefers more reliable source types:

1. `user_confirmed`
2. `imported`
3. `system_generated`
4. `executive_generated`
5. `sensor_observed`
6. `model_inferred`

Confidence still breaks ties after source priority. This keeps user-confirmed facts ahead of inferred facts when relevance is otherwise similar.

## Reranking

Retrieval builds typed candidates for facts and episodes. The candidate shape is intentionally generic so summaries can be added later without changing the ranking formula.

Current factors:

```text
score =
  0.30 * context_match +
  0.20 * entity_match +
  0.15 * recency +
  0.15 * salience +
  0.10 * confidence +
  0.05 * source_reliability +
  0.05 * retrieval_history_bonus
```

Factor behavior:

- `context_match`: token overlap between query text/structured fact text/tag cues and candidate text.
- `entity_match`: token overlap between `MemoryQuery.entities` and candidate entities.
- `recency`: normalized timestamp where available. Episodes use `end_ts`; facts currently have no first-class timestamp in the domain model.
- `salience`: episode salience where available. Facts currently have no first-class salience field.
- `confidence`: domain model confidence.
- `source_reliability`: source-type score where available. User-confirmed facts receive the highest value; model-inferred facts receive the lowest current value.
- `retrieval_history_bonus`: derived from matching `meta_memory` retrieval count when a meta-memory record exists.

Ranking is deterministic. Ties are broken by memory kind and memory ID.

`retrieve_memory()` still returns `facts` and `episodes` as separate lists and preserves the existing per-type `max_results` behavior. Internally it overfetches candidates, reranks them, then returns the top facts and top episodes.

When a returned fact or episode has a meta-memory record, retrieval increments `retrieval_count` and sets `last_retrieved_ts`. Ranking explanations show the meta-memory values used before the current retrieval update.

## Speakability Filtering

Retrieval uses `meta_memory.speakability` when a meta-memory record exists:

| Speakability | Ordinary retrieval |
|---|---|
| `normal` | Returned |
| `restricted` | Returned |
| `never_say` | Hidden |
| `internal_only` | Hidden |

`never_say` and `internal_only` can only be returned by a trusted internal query that explicitly includes internal records.

## Ranking Explanations

`MemoryBundle.ranking_explanations` is a JSON-friendly debug list for returned items.

Each explanation includes:

- `rank`
- `memory_kind`
- `memory_id`
- `score`
- `weights`
- `factors`
- `components`
- `matched_query_terms`
- `matched_entities`
- `source_type`
- `timestamp`
- `meta_memory`

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
- deterministic reranking order,
- ranking explanations,
- retrieval history bonus from meta-memory.
- retrieval count updates,
- speakability filtering and trusted internal override.

Useful targeted command:

```bash
python -m pytest tests/test_storage_retrieval.py
```
