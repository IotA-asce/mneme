# Testing

Verification run:

- `.venv/bin/python -m pytest tests/test_stage3_runtime.py` - passed, 6 tests.
- `.venv/bin/python -m pytest` - passed, 184 tests.
- `.venv/bin/python scripts/dev_check.py` - passed.
- `.venv/bin/mneme --db /tmp/mneme-stage3-cli2.sqlite3 run --json --input "remember that I like tea" --input "what do I like"` - passed, produced valid JSON timeline output with two scripted turns.
- `git diff --check` - passed.
