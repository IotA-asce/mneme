# Executive v0 Implementation Plan

## Phase 1: Intent models

- Add `ExecutiveMode`.
- Add `ExecutiveIntentType`.
- Add JSON-friendly `ExecutiveIntent`.

## Phase 2: Deterministic rule engine

- Add `Executive`.
- Consume working memory snapshots or live `WorkingMemory`.
- Track latest attention state from `attention_update`.
- Track world and safety state from runtime events.
- Emit only `executive_intent` runtime events.

## Phase 3: Initial arbitration rules

Priority order:

1. safety freeze
2. degraded safety mode
3. active user interaction
4. explicit memory instruction
5. listen to active speaker
6. look at current attention target
7. idle presence

Supported intents:

- `look_at_target`
- `listen`
- `respond_to_user`
- `remember_event`
- `idle_presence`
- `freeze_motion`
- `enter_degraded_mode`

## Phase 4: Validation and documentation

- Add tests for priority, preemption, degraded mode, supported fallback intents, and serialization.
- Document `docs/executive/EXECUTIVE_V0.md`.
- Update backlog and durable project memory.

## Validation steps

- `python -m pytest tests/test_executive.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

## Rollback notes

The implementation is isolated to a new executive module, package exports, tests, documentation, backlog, and memory records. Removing those additions returns prior runtime behavior.

## Definition of done

- Executive intent models exist and serialize cleanly.
- Deterministic executive rules publish intent only.
- Tests cover required priority and degraded-mode behavior.
- Documentation and project memory are updated.
