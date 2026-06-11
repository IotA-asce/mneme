# Implementation Plan

## Phase 1 — Inspect Existing Shape

- Read current models, tests, design docs, and interface drafts.
- Confirm existing scripts/tests construct valid model objects.

## Phase 2 — Add Model Boundary

- Add validation helpers for probability-like values, timestamps, source types, and memory statuses.
- Add direct validation in model `__post_init__` methods.
- Add `to_dict()` and `from_dict()` helpers for public model types.
- Preserve existing field names and dataclass construction style.

## Phase 3 — Verify Behavior

- Add tests for valid construction, invalid confidence/salience, empty summaries, timestamp ordering, enum conversion, and JSON round trips.
- Run the canonical developer check and individual smoke/test commands.

## Rollback

Revert `src/android_brain_memory/models.py`, `src/android_brain_memory/__init__.py`, and `tests/test_models.py` if validation proves too strict for known callers.

## Definition of Done

- Existing tests and scripts still pass.
- New model validation tests pass.
- Documentation explains the boundary.
- Backlog and project memory are updated.
