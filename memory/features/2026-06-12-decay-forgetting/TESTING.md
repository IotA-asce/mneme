# Testing

TDD: tests written first; observed ImportError (no decay module) before implementation.

- `python -m pytest tests/test_decay.py` — 9 passed.
- `python -m pytest` — 129 passed (full suite, no ranking regressions).
- `python scripts/dev_check.py` — run before merge.

Covered: downranking order + explanations, explicit downrank override, each suppression criterion gating independently (policy, retrieval count, age), user-confirmed immunity, purge tombstone shape + force gate, lifecycle event payloads, status setter and option validation.

Not verified: detail decay and raw-trace retention (documented future work); behavior over genuinely weeks-old databases (simulated via injected now_s).
