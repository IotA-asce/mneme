# Testing

Verification run:

- `.venv/bin/python -m pytest tests/test_attention.py` - passed, 5 tests.
- `.venv/bin/python -m pytest` - passed, 70 tests.
- `.venv/bin/python scripts/dev_check.py` - passed.
- `git diff --check` - passed.
