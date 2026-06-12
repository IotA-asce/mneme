# Changes

## Source

- `src/android_brain_memory/storage.py`
  - Added `RawTraceRecord` and `FactSupportRecord` dataclasses.
  - Added `PROVENANCE_MEMORY_KINDS` constant.
  - Added `get_raw_trace`, `get_recent_raw_traces`, `get_fact_support`, `get_facts_for_episode`, `get_episodes_in_window`, `get_provenance_chain`, `_provenance_node`, `_resolve_provenance_reference`, `_raw_trace_from_row`.
  - `store_raw_trace` gained an optional `created_ts` keyword (defaults to now).
- `src/android_brain_memory/__init__.py`
  - Exported `RawTraceRecord` and `FactSupportRecord`.

## Tests

- `tests/test_storage_provenance_reads.py` (new): raw trace round-trip and listing order/filter, direct fact support reads, reverse episode→fact lookup, window overlap and validation, fact→episode→trace chain traversal, missing-reference reporting, unknown root/kind errors.

## Docs

- `docs/memory/STORAGE.md`: boundary list, typed records, new "Raw Traces", "Fact Support Links", "Provenance Chains" sections, window query documentation.
- `docs/memory/PROVENANCE.md`: chain traversal section, testing list.
- `docs/architecture/ROADMAP.md`: Phase 1 marked implemented.
- `docs/architecture/REPO_STATUS.md`: implemented/partial lists updated.

## Planning

- `implement/storage-provenance-read-apis/` (CORE_IDEA, IMPLEMENT, RULES).
