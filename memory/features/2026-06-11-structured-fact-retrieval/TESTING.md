# Testing

Validation run:

- `git diff --check`
- `/tmp/mneme-validation-venv/bin/python -m pytest tests/test_models.py tests/test_storage_migrations.py tests/test_storage_retrieval.py`
- `/tmp/mneme-validation-venv/bin/python -m pytest`
- `/tmp/mneme-validation-venv/bin/python scripts/dev_check.py`

Coverage added:

- subject lookup,
- predicate lookup,
- object text lookup,
- tag filtering,
- source type filtering,
- user-confirmed source priority over inferred facts,
- default active status filtering,
- explicit non-active status retrieval warning,
- fact tag persistence through migration and ID lookup,
- model serialization with new fact/query fields.
