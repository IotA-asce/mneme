# Testing

TDD: tests written first; ImportError observed before implementation.

- `python -m pytest tests/test_dialogue.py` — 9 passed.
- `python -m pytest` — 171 passed.
- `python scripts/dev_check.py` — run before merge.

Covered: answer slots/refs/text, clarify on conflict warnings, acknowledgments (instruction + remember_event intent), greetings, silence for frozen/degraded/listen/look/idle and degraded respond intents, restricted-fact exclusion from spoken refs, full executive→planner integration, determinism.

Not verified: speech timing/realization quality (Stage 5); multi-turn strategy (future).
