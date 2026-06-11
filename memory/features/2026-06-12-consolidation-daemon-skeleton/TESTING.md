# Testing

Validation run:

- `git diff --check`
- `/tmp/mneme-validation-venv/bin/python -m pytest tests/test_consolidation.py tests/test_storage_migrations.py`
- `/tmp/mneme-validation-venv/bin/python -m pytest`
- `/tmp/mneme-validation-venv/bin/python scripts/dev_check.py`
- `/tmp/mneme-validation-venv/bin/python scripts/consolidate_once.py`

Coverage added:

- repeated tagged episodes creating one summary,
- source episodes remaining active,
- summary meta-memory preserving supporting episode IDs,
- decay/downranking metadata written to non-representative episodes,
- repeated runs updating the same deterministic summary instead of creating duplicates.
