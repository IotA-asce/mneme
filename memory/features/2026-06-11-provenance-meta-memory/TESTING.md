# Testing

Validation run:

- `git diff --check`
- `/tmp/mneme-validation-venv/bin/python -m pytest tests/test_models.py tests/test_storage_migrations.py tests/test_storage_retrieval.py`
- `/tmp/mneme-validation-venv/bin/python -m pytest`
- `/tmp/mneme-validation-venv/bin/python scripts/dev_check.py`

Coverage added:

- provenance normalization and preservation for raw traces, episodes, facts, and summaries,
- secret-like provenance key rejection,
- invalid provenance rejection before related memory rows are persisted,
- typed speakability parsing and model serialization,
- retrieval count and last-retrieved timestamp updates,
- default filtering for `never_say` and `internal_only`,
- trusted internal override for internal retrieval.
