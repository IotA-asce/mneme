# Testing

Validation commands for this feature:

```bash
python -m pytest tests/test_storage_migrations.py
python -m pytest
python scripts/dev_check.py
python scripts/init_db.py
python scripts/smoke_test_memory.py
git diff --check
```

Expected coverage:

- migration tracking and idempotence,
- checksum mismatch rejection,
- meta-memory write/read/update,
- working context snapshot write/recent-read behavior,
- episode and fact ID lookup,
- preservation of source type, status, confidence, and support/provenance fields,
- existing smoke scripts and retrieval tests.
