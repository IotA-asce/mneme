# Implementation Plan

## Phase 1 — Habituation

- Per-target exposure counter incremented on each sighting; novelty = 1.0 on first sighting, then `max(0.0, 0.5 ** prior_exposures)`; used by perception/safety/goal/world-state target builders.

## Phase 2 — Inhibition of Return

- `_activate()` records the previously active target into an inhibition map (`target_id → inhibited_until_ts`, window `ior_ms` default 2000, penalty `ior_penalty` default 0.15).
- Target builders subtract the penalty (floored at 0) while inhibited and set `factors["inhibition_of_return"] = 1.0`; expired inhibitions purge in `expire()`.

## Phase 3 — Curiosity (opt-in)

- `enable_curiosity=False` constructor flag; `idle_tick(now_ms=None)` runs selection without an event.
- With curiosity enabled and no live targets, selection activates a synthetic transient target rotating `scan_left` → `scan_center` → `scan_right` (`curiosity:<label>`, type `curiosity`, priority 0.05, reason `curiosity_idle`). Real targets always win.

## Phase 4 — History

- Bounded `state_history` (default 64) recording state_id, created_ts, active_target_id, reason on every state build.

## Phase 5 — Tests (written first) and Docs

- `tests/test_attention_v1.py`: habituation decline, IOR penalty + expiry, curiosity rotation + preemption by real targets + opt-out default, history recording/bounding.
- Update `docs/attention/ATTENTION_MANAGER.md`, `MASTER_ROADMAP.md` M2.3, `REPO_STATUS.md`, memory entry + index.

## Validation

`python -m pytest tests/test_attention_v1.py tests/test_attention.py` → full suite → dev_check.

## Rollback

Revert attention.py changes and new tests/docs; all changes additive.

## Definition of Done

Attention traces over scripted scenarios match documented expectations; v0 tests pass unchanged; full suite passes.
