# Testing

Targeted tests:

```bash
.venv/bin/python -m pytest tests/test_conversational_presence.py -q
```

Full verification should include:

```bash
git diff --check
.venv/bin/python scripts/dev_check.py
```

Result during implementation: both passed; `scripts/dev_check.py` completed DB init, smoke test, and 280 pytest tests.
