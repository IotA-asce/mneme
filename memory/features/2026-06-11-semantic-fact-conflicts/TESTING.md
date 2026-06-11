# Testing

Validation run:

- `git diff --check`
- `/tmp/mneme-validation-venv/bin/python -m pytest tests/test_models.py tests/test_storage_migrations.py tests/test_storage_retrieval.py`
- `/tmp/mneme-validation-venv/bin/python -m pytest`
- `/tmp/mneme-validation-venv/bin/python scripts/dev_check.py`

Coverage added:

- inferred fact superseded by user-confirmed fact,
- confirmed-versus-confirmed conflict preservation,
- duplicate semantic facts remain non-conflicting,
- context-specific facts remain non-conflicting,
- `supersedes_fact_id` read/write behavior,
- conflict report query behavior.
