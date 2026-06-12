# Changes

## Source

- `src/android_brain_memory/models.py`: `MemoryBundle.summaries` field (validated JSON mapping list, default empty) with `to_dict`/`from_dict` support.
- `src/android_brain_memory/storage.py`: `search_memory_summaries()`; `MemorySummaryRecord.to_dict()`.
- `src/android_brain_memory/retrieval.py`:
  - summary retrieval candidates (kind `summary`) built when `include_summaries` and `query_text` are set,
  - `_conflict_warnings()` over returned fact statement groups,
  - `_build_provenance_summary()` deriving bundle provenance from `get_provenance_chain`,
  - empty-result and speakability-withheld warnings,
  - `found N summary(ies)` bundle summary part.

## Tests

- `tests/test_retrieval_warnings_summaries.py` (new): summary search, ranked summary inclusion + history updates, `include_summaries=False`, internal-only summary filtering with withheld warning, empty-result warning, conflict warnings, derived provenance summary, no-links fallback, bundle round-trip.
- `tests/test_storage_retrieval.py`: two assertions updated to the new intended behavior (derived provenance summary text; added conflict warning in explicit conflicted-status query).

## Docs

- `docs/memory/RETRIEVAL.md`: boundary, summary retrieval, warnings, provenance summary sections.
- `docs/memory/PROVENANCE.md`, `docs/memory/STORAGE.md`: summary retrieval no longer future work; `search_memory_summaries` documented.
- `docs/architecture/ROADMAP.md`: Phase 4 fully checked; Phase 2 status reflects implemented window query.
- `docs/architecture/REPO_STATUS.md`: retrieval manager status updated.

## Planning

- `implement/retrieval-warnings-summaries/` (CORE_IDEA, IMPLEMENT, RULES).
