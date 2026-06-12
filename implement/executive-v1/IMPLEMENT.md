# Implementation Plan

## Phase 1 — Goal Stack

- `ExecutiveGoal` dataclass (goal_id, goal_type, created_ts, status active/suspended/completed, payload, `to_dict()`).
- `Executive.push_goal/complete_goal/current_goal`; `_select_intent` wraps the v0 rule selection: normal-mode intents get `active_goal_id`/`active_goal_type`; safety-mode intents suspend active goals (`suspended_goal_ids`); the first normal intent after suspension reactivates and carries `resumed_goal`.

## Phase 2 — Response Timing

- `min_response_delay_ms` (default 0): inside the respond rule, a user turn younger than the delay yields LISTEN with reason `awaiting_turn_completion`.

## Phase 3 — Memory-Informed Intents

- Optional `engine` (MnemeMemory): RESPOND_TO_USER retrieves (`query_text=turn text`, `requester="executive"`, `max_results=3`), attaches `payload["memory"]` = {fact_ids, episode_ids, summary_ids, warnings, provenance_summary, needs_clarification}; bundle kept on `last_memory_bundle`.

## Phase 4 — Idle Rotation

- IDLE_PRESENCE payload rotates `idle_behavior` through `ambient_scan`/`rest_pose`/`micro_motion` by counter.

## Phase 5 — Tests (written first) and Docs

- `tests/test_executive_v1.py`: goal context, suspend/resume across safety freeze, timing gate, memory payload + clarification flag, idle rotation, v0 defaults preserved.
- Docs: `docs/executive/EXECUTIVE_V0.md` v1 section, `MASTER_ROADMAP.md` M2.4, `REPO_STATUS.md`, memory entry + index.

## Validation

`python -m pytest tests/test_executive_v1.py tests/test_executive.py` → full suite → dev_check.

## Rollback

Revert executive.py changes and new tests/docs; all additive.

## Definition of Done

Preemption, resumption, timing, and memory-informed behavior covered by deterministic tests; v0 tests pass unchanged; full suite passes.
