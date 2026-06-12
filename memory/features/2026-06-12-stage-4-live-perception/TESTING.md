# Testing

Verification run:

- `.venv/bin/python -m pytest tests/test_live_perception.py tests/test_real_peripherals.py tests/test_stage3_runtime.py` - passed, 18 tests.
- `.venv/bin/mneme --db /tmp/mneme-stage4-live-cli2.sqlite3 run --json --speech-command "printf '{\"speaker\":\"user\",\"transcript\":\"remember that I like chai\",\"confidence\":0.9}'" --input "hello"` - passed, produced live speech transcript events and a memory candidate.
- `.venv/bin/python scripts/dev_check.py` - passed, including 196 pytest tests.
- `git diff --check` - passed.
