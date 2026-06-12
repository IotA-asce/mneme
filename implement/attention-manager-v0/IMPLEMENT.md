# Attention Manager v0 Implementation Plan

## Phase 1: Runtime attention model

- Add `AttentionTarget` and `AttentionState` dataclasses.
- Include JSON serialization helpers and validation for timestamps, confidence, priority, and mappings.
- Represent ranking explanations with feature factors and weighted components.

## Phase 2: Deterministic manager

- Add `AttentionManager`.
- Subscribe to local perception, world-state, executive intent, skill goal, and safety events.
- Convert relevant events into candidate targets.
- Score targets using active speaker, sound event, face/person presence, explicit user address, safety relevance, novelty, current goal, and confidence.
- Publish `attention_update` events with state payloads only.

## Phase 3: Stabilization behavior

- Add target TTL expiry.
- Add dwell/lock behavior to avoid rapid target flicker.
- Allow safety relevance and materially higher priority to override a current dwell lock.

## Phase 4: Validation and documentation

- Add tests for social focus, safety override, dwell lock, expiry, and serialization.
- Document runtime boundaries in `docs/attention/ATTENTION_MANAGER.md`.
- Update backlog and durable project memory.

## Validation steps

- `python -m pytest tests/test_attention.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

## Rollback notes

The feature is isolated to a new attention module, package exports, tests, docs, backlog, and memory. Removing those files and export entries returns the prior runtime behavior.

## Definition of done

- Attention state models exist and serialize cleanly.
- Manager publishes runtime attention state without actuator commands.
- Required behavior tests pass.
- Documentation, backlog, and memory index are updated.
