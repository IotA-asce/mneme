# Testing

Verification for this feature:

```bash
python scripts/dev_check.py
python scripts/init_db.py
python scripts/smoke_test_memory.py
python -m pytest
git diff --check
```

CI uses Python 3.11 and runs:

```bash
python -m pip install -e '.[dev]'
python scripts/init_db.py
python scripts/smoke_test_memory.py
python -m pytest
```
