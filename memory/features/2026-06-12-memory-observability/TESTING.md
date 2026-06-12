# Testing

TDD: tests written first; 6 observed failing (missing engine kwarg, storage method, CLI commands) before implementation. One test was corrected during green: the content-leak assertion initially used a fact ID containing the content word ("fact_tea"), making the check trip on the legitimate ID — fixed to a content-free ID so the assertion tests what it means.

- `python -m pytest tests/test_observability.py` — 6 passed.
- `python -m pytest` — 135 passed (full suite).
- `python scripts/dev_check.py` — run before merge.

Covered: retrieval event payload shape and content-leak guard, conflict events on conflicting upserts, unchanged no-bus behavior, decay meta listing, CLI provenance chain and decay output as parsed JSON.

Not verified: event persistence (the stream is in-memory; durable event logging is future work).
