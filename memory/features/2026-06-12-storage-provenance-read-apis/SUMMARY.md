# Summary: Storage and Provenance Read APIs

Date: 2026-06-12
Type: Feature
Status: Complete

Added the missing read side of the storage/provenance baseline (roadmap Phase 1):

- `RawTraceRecord` and `FactSupportRecord` typed read models.
- `get_raw_trace()` and `get_recent_raw_traces()` (newest first, optional source-type filter).
- `get_fact_support()` and `get_facts_for_episode()` for direct fact support link reads in both directions.
- `get_episodes_in_window()` with overlap semantics and optional status filter.
- `get_provenance_chain()` — read-only, cycle-safe, deterministic traversal that reconstructs fact → episode → raw trace derivations from `fact_support` and meta-memory `supporting_memory_ids`, reporting unresolvable references under `missing`.
- Optional `created_ts` keyword on `store_raw_trace()` for deterministic replay/test timestamps.

No schema changes, no new dependencies, no changes to write behavior or retrieval ranking.

This closes the roadmap Phase 1 exit criteria: a stored candidate can be traced from raw trace to episode to fact support, and tests prove support links can be read directly.
