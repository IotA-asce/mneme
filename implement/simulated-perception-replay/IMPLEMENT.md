# Simulated Perception Replay Implementation Plan

Date: 2026-06-12
Status: Implemented in this feature branch

## Plan

1. Add `src/android_brain_memory/simulation.py`.
2. Implement deterministic simulated worker classes for face/person, speech, sound direction, touch, and body/internal health.
3. Define scenario loading for YAML and JSON files.
4. Add `ScenarioReplayRunner` that reads scenario steps and publishes events through `EventBus`.
5. Add explicit memory candidate emission for scenario steps marked important or carrying candidate data.
6. Add a scenario fixture for a basic conversation.
7. Add tests proving replay updates sensory echo and working memory and emits memory candidates.
8. Document the scenario format in `docs/runbooks/SCENARIO_REPLAY.md`.
9. Update backlog and project memory.

## Validation

- `python -m pytest tests/test_scenario_replay.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

## Rollback

Remove the simulation module, fixture, tests, docs, implementation plan, and project memory entry. No migrations or dependencies are added.

## Definition of Done

- A YAML scenario can replay a conversation deterministically.
- Echo and working memory update through the event bus.
- Important steps can produce memory candidate events.
- Documentation and project memory are updated.
