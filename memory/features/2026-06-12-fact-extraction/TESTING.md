# Testing

TDD: tests written first; observed ImportError (no extraction module) before implementation.

- `python -m pytest tests/test_fact_extraction.py` — 7 passed.
- `python -m pytest` — 114 passed (full suite).
- `python scripts/dev_check.py` — run before merge.

Not verified: extraction from consolidation summaries (future increment); free-text statements (explicit non-goal).
