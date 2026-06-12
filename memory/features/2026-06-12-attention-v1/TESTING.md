# Testing

TDD: tests written first; 6 failures (unknown kwargs/methods) observed before implementation.

- `python -m pytest tests/test_attention_v1.py tests/test_attention.py` — 11 passed (v0 tests unchanged).
- `python -m pytest` — 155 passed.
- `python scripts/dev_check.py` — run before merge.

Covered: monotonic habituation decline, IOR factor + recovery outside the window, safety override immunity to IOR, curiosity rotation/preemption/default-off, history shape and bounding.

Not verified: tuned habituation/IOR constants against real-world feel (Stage 5 behavior integration will revisit); learned adaptation (Stage 7 non-goal here).
