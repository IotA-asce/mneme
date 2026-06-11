# Testing

Recommended verification commands for this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/init_db.py
python scripts/smoke_test_memory.py
python -m pytest
```

For environments where the package is not installed but dependencies are already available:

```bash
PYTHONPATH=src python3 scripts/init_db.py
PYTHONPATH=src python3 scripts/smoke_test_memory.py
PYTHONPATH=src python3 -m pytest
```

The audit itself should be verified by running the smoke script and pytest suite. Markdown files should be manually inspected for accurate links, current status, and no claims of unimplemented behavior as complete.
