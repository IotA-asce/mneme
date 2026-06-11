# Testing

Validation commands for this change:

```bash
python -m pytest
python scripts/dev_check.py
python scripts/init_db.py
python scripts/smoke_test_memory.py
git diff --check
```

Expected coverage:

- valid model construction,
- invalid confidence and salience values,
- empty summaries,
- timestamp ordering,
- source type and status enum conversion,
- JSON round trips for public model types,
- existing storage/retrieval scripts and tests.
