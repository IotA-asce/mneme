# Core Idea: Attention Manager v1 (Stage 2 / M2.3)

## Problem Statement

Attention v0 selects targets with static factors: novelty is binary (new=1.0, seen=0.25 forever), nothing penalizes returning to a just-abandoned focus (flicker risk beyond dwell), idle means "no target" rather than lifelike scanning, and there is no record of how focus evolved for explainability.

## Desired Outcome

Additive v1 behaviors, all deterministic:

- **Habituation**: per-target exposure counts decay novelty geometrically (1.0 → 0.5 → 0.25 → …) so repeated stimuli fade.
- **Inhibition of return**: after focus switches away from a target, that target is priority-penalized for a configurable window, with an explicit `inhibition_of_return` factor in explanations.
- **Curiosity during idle** (opt-in `enable_curiosity`): with no real targets, `idle_tick()` activates synthetic curiosity scan targets rotating deterministically (`scan_left`/`scan_center`/`scan_right`); any real target immediately wins.
- **State history**: bounded record of (state_id, created_ts, active_target_id, reason) transitions for explainability.

## Affected Systems

- `src/android_brain_memory/attention.py`, `tests/test_attention_v1.py` (new)
- `docs/attention/ATTENTION_MANAGER.md`, roadmap/status docs

## Assumptions / Constraints

- v0 contracts preserved: existing tests untouched; curiosity is opt-in because v0 promises `active_target_id is None` when idle.
- Attention still publishes state only — no gaze or actuator commands.
- Safety override behavior is unchanged and is never penalized by IOR or habituation gating.

## Non-Goals

- Learned/adaptive habituation rates (procedural learning is Stage 7).
- Gaze dynamics (skills, Stage 5).

## Risks

- Habituation curve changes relative priorities of re-seen targets; no existing test pins those values, and ordering-relevant tests still pass (verified by the full suite).
