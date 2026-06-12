# Testing

Validation should include:

- `python -m pytest tests/test_working_memory.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

Coverage added:

- sensory echo TTL expiry,
- sensory echo capacity trimming,
- event bus subscription filtering into echo,
- working-memory event updates,
- bounded recent dialogue turns,
- bounded recent event references,
- skill goal/status context,
- snapshot export,
- snapshot persistence through SQLite `working_context_snapshot`.
