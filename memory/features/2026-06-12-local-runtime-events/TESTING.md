# Testing

Validation should include:

- `python -m pytest tests/test_runtime_events.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

Coverage added:

- publication and subscriber delivery,
- subscription filters by kind, topic, and source,
- deterministic sequence ordering,
- TTL expiry filtering and pruning,
- all required event categories,
- JSON-friendly event serialization round trips,
- confidence validation,
- topic/kind boundary validation.
