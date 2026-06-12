# Summary: Working Memory Lifecycle v1 (Stage 2 / M2.2)

Date: 2026-06-12
Type: Feature
Status: Complete

Added `ContextWindowManager` (`src/android_brain_memory/context_windows.py`): interactions are now bounded into context windows. A window opens when an interaction-relevant perception event (speech, person seen, touch) arrives, stays alive while activity continues, and closes after an idle timeout (default 8s, caller-driven `tick()` with injected clock) or an explicit `close_now(reason)`. At every close boundary a working-memory snapshot is persisted automatically via the existing `persist_snapshot()` path and the window records its `snapshot_id`. Transitions are published as `world_state_update` events (`state_key="context_window"`); closed windows live in a bounded history.

One window at a time in V1; non-interaction events (body health, sound alone) never open windows. The manager owns lifecycle only — `WorkingMemory` content handling is untouched.
