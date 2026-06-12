# Testing

Verification run:

- `.venv/bin/python -m pytest tests/test_real_peripherals.py tests/test_stage3_runtime.py` - passed, 12 tests.
- `.venv/bin/mneme --db /tmp/mneme-stage4-real2.sqlite3 run --device-backend real --json --input "hello"` - passed on the local macOS host; detected 1 camera, 1 microphone, and 3 speakers.
- `.venv/bin/python scripts/dev_check.py` - passed, including 190 pytest tests.
- `git diff --check` - passed.
