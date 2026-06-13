# Testing

Verified:

- `.venv/bin/python -m pytest tests/test_stage6_local_living_lab.py tests/test_live_perception.py tests/test_conversational_presence.py`
- `.venv/bin/python scripts/dev_check.py`
- manual local UI smoke with:
  - `GET /`,
  - `GET /state`,
  - `POST /devices`,
  - `POST /input`.

The focused tests prove preference persistence, preferred microphone selection, preferred speaker selection, and UI rendering of selected devices.
