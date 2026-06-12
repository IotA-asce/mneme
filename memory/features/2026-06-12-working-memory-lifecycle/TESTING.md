# Testing

TDD: tests written first; ImportError observed before implementation.

- `python -m pytest tests/test_context_windows.py` — 7 passed.
- `python -m pytest` — 149 passed.
- `python scripts/dev_check.py` — run before merge.

Covered: open-on-speech, activity extension, idle-timeout close with persisted snapshot + history, reopen after close, published transitions, non-interaction events ignored, manual close reasons, replay-fixture window with snapshot content (speaker + dialogue turns).

Not verified: multi-party concurrent windows (V1 non-goal); window→episode bridging (documented future work).
