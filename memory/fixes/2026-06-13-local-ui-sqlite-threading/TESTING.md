# Testing

Verified:

- `.venv/bin/python -m pytest tests/test_stage6_local_living_lab.py`
- Manual UI smoke:
  - start `mneme --db /tmp/mneme-ui-threading.sqlite3 ui --port 8876`,
  - fetch `http://127.0.0.1:8876/`,
  - fetch `http://127.0.0.1:8876/state`,
  - POST `text=hello Mneme` to `/input`.

The manual smoke returned HTML, JSON state, and HTTP 303 redirect for the input post without SQLite thread errors.
