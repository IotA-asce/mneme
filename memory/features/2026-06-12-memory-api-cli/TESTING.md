# Testing

Validation run for this feature should include:

- `python -m pytest tests/test_memory_engine_cli.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `python scripts/mneme_memory.py inspect-db`

Coverage added:

- facade initialization through tracked migrations,
- candidate scoring with explicit remember promotion,
- raw trace storage from a candidate,
- candidate-to-episode encoding,
- episode storage,
- fact upsert,
- retrieval with ranking explanations,
- one-shot consolidation creating a summary,
- CLI JSON output for the same conversation-like flow,
- database inspection counts.
