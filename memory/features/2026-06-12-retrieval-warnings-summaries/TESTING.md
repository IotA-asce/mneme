# Testing

Tests were written first and observed failing (9 failures: missing `summaries` kwarg, missing `search_memory_summaries`, missing warnings) before implementation.

Commands run:

- `python -m pytest tests/test_retrieval_warnings_summaries.py` — 9 passed.
- `python -m pytest` — 96 passed (full suite).
- `python scripts/dev_check.py` — completed successfully (run before merge).

Behavioral note: two pre-existing assertions in `tests/test_storage_retrieval.py` encoded the old hardcoded provenance sentence and the warnings list without conflict warnings. These asserted behavior this feature intentionally replaces, so they were updated to the new expected values (not weakened — both are now stricter).

Covered behavior:

- Summary search matches summary text and scope key, ordered deterministically.
- Ranked summaries appear in bundles with explanations and increment summary meta-memory retrieval counts.
- `include_summaries=False` and empty `query_text` skip summary retrieval.
- Internal-only summaries are withheld with a count-only warning.
- Empty retrieval, conflicted statement groups, and non-active status filters warn deterministically.
- Provenance summary contains real `supported_by` / `derived_from` edges, with an explicit no-links fallback.
- `MemoryBundle` round-trips `summaries` through `to_dict`/`from_dict`.

Not verified (out of scope): retrieval-time use of consolidation decay hints; summary retrieval through structured fact-only queries (intentionally skipped).
