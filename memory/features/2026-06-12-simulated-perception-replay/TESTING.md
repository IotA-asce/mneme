# Testing

Validation should include:

- `python -m pytest tests/test_scenario_replay.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `python scripts/replay_scenario.py tests/fixtures/basic_conversation.yaml`
- `git diff --check`

Coverage added:

- YAML scenario loading,
- JSON scenario loading,
- deterministic event order,
- simulated face/person, speech, sound, touch, and health events,
- safety event emission from health steps,
- event bus publication through replay,
- sensory echo updates through subscription,
- working memory updates through subscription,
- explicit memory candidate emission from important scenario steps.
