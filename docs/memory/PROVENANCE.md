# Memory Provenance and Meta-Memory

Status: V1 local SQLite prototype

Mneme preserves provenance and meta-memory beside stored memory records. This is not encryption or a complete privacy system yet. It is the structured audit layer future policy enforcement can build on.

## Boundary

The provenance/meta-memory layer owns:

- `meta_memory` records for stored memories,
- provenance JSON normalization,
- speakability policy flags,
- retrieval count and last-retrieved tracking.

It does not own:

- cryptographic protection,
- secret storage,
- user consent workflows,
- conflict resolution,
- actuator behavior.

## Meta-Memory Records

`MetaMemoryRecord` tracks:

- `memory_id`
- `memory_kind`
- `source_type`
- `provenance_json`
- `last_retrieved_ts`
- `retrieval_count`
- `contradiction_score`
- `speakability`

Storage helpers can write meta-memory while storing:

- raw traces,
- episodes,
- facts,
- summaries.

Existing direct `write_meta_memory()` calls remain available.

## Provenance Shape

`provenance_json` is normalized to include:

- `source_type`
- `source_id`
- `derivation_path`
- `supporting_memory_ids`
- `notes`

Additional non-secret keys may be preserved. Provenance keys that look secret-bearing, such as token/password/credential/api-key fields, are rejected. Do not store secrets, private credentials, tokens, or keys in provenance.

Storage validates provenance metadata before writing the associated memory row, so rejected provenance should not leave a partial raw trace, episode, fact, or summary behind.

Example:

```json
{
  "source_type": "user_confirmed",
  "source_id": "dialogue_001",
  "derivation_path": ["raw_trace", "episode", "fact"],
  "supporting_memory_ids": ["trace_001", "ep_001"],
  "notes": "Fact derived from a user-confirmed episode."
}
```

## Speakability

Supported values:

- `normal`: safe for ordinary retrieval and use.
- `restricted`: retrievable by ordinary retrieval, but caller policy should treat it carefully.
- `never_say`: hidden from ordinary retrieval.
- `internal_only`: hidden from ordinary retrieval.

Retrieval excludes `never_say` and `internal_only` records unless the query is both:

- `trusted_internal=True`
- `include_internal=True`

This is a policy hook, not a complete authorization system.

## Retrieval Updates

When `retrieve_memory()` returns a fact or episode with a meta-memory record, retrieval updates:

- `retrieval_count`
- `last_retrieved_ts`

Retrieval history is also used as a small ranking factor. The ranking explanation reflects the history available before the current retrieval update.

## Summary Support

`store_memory_summary()` writes `memory_summary` rows and can write corresponding meta-memory records. Summary retrieval is still future work.

## Provenance Chain Traversal

`MemoryStore.get_provenance_chain(memory_id, memory_kind)` reconstructs the derivation path of a stored memory from data that is already persisted:

- fact → episode edges come from `fact_support` (`supported_by`),
- episode → raw trace (and other) edges come from normalized `supporting_memory_ids` in meta-memory (`derived_from`),
- references that no longer resolve (for example echo-only traces that were never persisted) are listed under `missing`.

This satisfies the Phase 1 exit criterion that a stored candidate can be traced from raw trace to episode to fact support. The traversal is read-only; it reports stored provenance and never invents or repairs links.

See `docs/memory/STORAGE.md` for the read API surface (`get_raw_trace`, `get_recent_raw_traces`, `get_fact_support`, `get_facts_for_episode`, `get_episodes_in_window`).

## Testing

Current tests cover:

- provenance normalization for raw traces, episodes, facts, and summaries,
- secret-like provenance key rejection,
- retrieval count updates,
- speakability filtering,
- trusted internal retrieval override,
- raw trace and fact support read APIs,
- episode time-window retrieval,
- end-to-end fact → episode → raw trace chain traversal and missing-reference reporting.
