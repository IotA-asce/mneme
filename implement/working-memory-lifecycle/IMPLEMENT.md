# Implementation Plan

## Phase 1 — Context Windows

- `context_windows.py`: `ContextWindow` dataclass (window_id, opened_ts, trigger, last_activity_ts, closed_ts, close_reason, snapshot_id, event_count, `to_dict()`), and `ContextWindowManager(working_memory, *, store=None, bus=None, idle_timeout_ms=8000, max_history=32, source="context_windows", clock=None)`:
  - `attach_to_bus` subscribing to `perception_observation`,
  - interaction events (`speech_transcript`, `person_seen`, `touch`) open a window when none is open and refresh `last_activity_ts`/`event_count` when one is,
  - `tick(now_ms=None)` closes the window after `idle_timeout_ms` of inactivity: persists a working-memory snapshot to the store (when provided), records `snapshot_id`, moves the window to bounded history,
  - `close_now(reason)` manual boundary,
  - window open/close published as `world_state_update` events with `state_key="context_window"`.

## Phase 2 — Tests (written first)

- `tests/test_context_windows.py`: open on speech, activity extends, idle close persists snapshot + history, reopen after close, published events, non-interaction events ignored, replay-fixture end-to-end with persisted snapshot content.

## Phase 3 — Docs

- `docs/memory/WORKING_MEMORY.md` lifecycle section; `MASTER_ROADMAP.md` M2.2; `REPO_STATUS.md`; memory entry + index.

## Validation

`python -m pytest tests/test_context_windows.py` → full suite → dev_check.

## Rollback

Revert new module/tests/docs. No schema changes (uses existing `working_context_snapshot` table).

## Definition of Done

Conversation-shaped replay produces correct context windows and automatically persisted snapshots; full suite passes.
