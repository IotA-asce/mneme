# Testing

Targeted and full verification were run before merge:

- `.venv/bin/python -m pytest tests/test_cognitive_benchmarks.py tests/test_turn_understanding.py tests/test_memory_review.py tests/test_capability_ladder.py` — 13 passed.
- `.venv/bin/mneme eval cognition --fixture tests/fixtures/cognition/basic_preference_recall.yaml --json` — passed with total score 1.0 and conservative L2 evidence for the narrow fixture.
- `.venv/bin/mneme eval capability --json` — reported L2 evidence for the bundled benchmark and explicitly left L3-L8 unproven.
- `git diff --check` — passed.
- `.venv/bin/python scripts/dev_check.py` — database init and smoke test passed; 261 pytest tests passed.
