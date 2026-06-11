# Testing

Validation run:

- `git diff --check`
- `/tmp/mneme-validation-venv/bin/python -m pytest tests/test_models.py tests/test_storage_retrieval.py`
- `/tmp/mneme-validation-venv/bin/python -m pytest`
- `/tmp/mneme-validation-venv/bin/python scripts/dev_check.py`

Coverage added:

- deterministic episode reranking,
- ranking factor explanations,
- weighted component explanations,
- matched entity reporting,
- meta-memory retrieval history bonus,
- model serialization for `MemoryBundle.ranking_explanations`.
