# Memory Retrieval

Status: V1 deterministic SQLite retrieval

Mneme's current retrieval layer is local and deterministic. It uses structured SQLite queries over facts and basic text search over episodes. It does not use embeddings, vector search, LLM reranking, or external services.

## Boundary

The retrieval layer owns:

- accepting `MemoryQuery` objects,
- querying local fact, episode, and memory summary storage,
- filtering ordinary fact retrieval to active facts by default,
- filtering internal-only speakability records by default,
- building retrieval candidates,
- applying deterministic reranking,
- updating meta-memory retrieval counters for returned items,
- emitting warnings for empty, withheld, non-active, and conflicting results,
- deriving the bundle provenance summary from stored provenance chains,
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

## Summary Retrieval

When `MemoryQuery.include_summaries` is set (the default) and `query_text` is non-empty, retrieval also searches `memory_summary` rows over summary text and scope key. Matching summaries are ranked with the same weighted factors as facts and episodes (timestamp uses `end_ts` falling back to `created_ts`; summaries have no entity list or salience).

Returned summaries appear in `MemoryBundle.summaries` as JSON-friendly dicts, capped by `max_results`, with ranking explanations of kind `summary`. Speakability filtering and retrieval-history updates apply to summaries exactly as they do to facts and episodes through their `summary` meta-memory records.

Structured fact-only queries with an empty `query_text` skip summary retrieval, mirroring episode behavior.

## Warnings

`MemoryBundle.warnings` reports retrieval conditions deterministically:

- nothing matched: `no matching memory found for this query`,
- speakability policy withheld candidates: `N candidate(s) withheld by speakability policy` (a count only; withheld content and IDs are never included),
- non-active facts returned via an explicit status filter (existing behavior),
- returned facts whose subject/predicate group has conflicted records: `conflicting fact records exist for <subject> <predicate>`, one warning per statement group.

Warnings surface conditions for callers and debugging. They do not trigger conflict resolution or memory mutation.

## Provenance Summary

`MemoryBundle.provenance_summary` is derived from stored provenance chains (`get_provenance_chain`) for the returned facts, episodes, and summaries. Edge lines such as `fact f supported_by episode e` and `episode e derived_from raw_trace t` are deduplicated and joined deterministically. When returned memories have no stored provenance links, the summary says so explicitly instead of implying provenance exists.

## Reranking

Retrieval builds typed candidates for facts, episodes, and memory summaries using one shared candidate shape and ranking formula.

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

`retrieve_memory()` returns `facts`, `episodes`, and `summaries` as separate lists and preserves the existing per-type `max_results` behavior. Internally it overfetches candidates, reranks them, then returns the top items of each kind.

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
