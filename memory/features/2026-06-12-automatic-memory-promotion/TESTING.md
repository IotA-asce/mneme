# Testing

TDD: `tests/test_promotion.py` was written first and observed failing (ImportError: no `promotion` module / `memory_lifecycle_event`) before implementation.

Commands run:

- `python -m pytest tests/test_promotion.py` — 8 passed.
- `python -m pytest` — 107 passed (full suite).
- `python scripts/dev_check.py` — run before merge.

Covered: decision→storage mapping for all four salience decisions, bus subscription handling, lifecycle event kind/topic/payload, malformed candidate tolerance (skipped, counted, no raise), and scenario replay producing a durable episode with provenance chain to its raw trace without manual storage calls.

Not verified: behavior under perception-rate event storms (V1 is bench/replay only); promotion of candidates arriving while the engine's SQLite file is locked by another process (single-process assumption documented).
