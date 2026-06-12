# Testing

TDD: tests written first; observed ImportError (no consolidation_daemon module) before implementation.

- `python -m pytest tests/test_consolidation_daemon.py` — 6 passed.
- `python -m pytest` — 120 passed (full suite).
- `python scripts/dev_check.py` — run before merge.

Not verified: long-running operation behind a real timer/thread (intentionally out of scope until Stage 3); idle-triggered scheduling (Stage 2 dependency).
