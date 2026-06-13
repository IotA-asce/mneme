# Testing

Planned validation:

- `python -m pytest tests/test_dialogue.py tests/test_stage6_local_living_lab.py tests/test_real_peripherals.py`
- `python -m compileall -q src/android_brain_memory`
- `python scripts/dev_check.py`

Manual smoke:

- Run `mneme ui`, confirm real/fake device options render.
- Press **Refresh list** and confirm the options remain or update.
